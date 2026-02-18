#!/usr/bin/env python3

import http.server
import socketserver
import json
import subprocess
import threading
import time
import os
from urllib.parse import urlparse
from datetime import datetime

PORT = 8765

# GitHub CLI path (may not be in PATH for non-interactive shells)
GH_CLI = '/opt/homebrew/bin/gh'

# Cache for build status (aggressive caching to avoid rate limits)
cache = {}
cache_time = {}
CACHE_DURATION = 300  # 5 minutes (was 60 seconds)
rate_limited_until = 0  # Track when rate limit expires

# Track runner states to detect job completion
runner_states = {}  # {runner_name: {'busy': bool, 'project': str, 'last_check': timestamp}}

apps = [
    # Lucky Jackpot Casino Games
    {'name': 'blackjack21', 'aabOffset': 200, 'amazonOffset': 100, 'studio': 'LJC'},
    {'name': 'keno4card', 'aabOffset': 300, 'amazonOffset': 200, 'studio': 'LJC'},
    {'name': 'keno20card', 'aabOffset': 400, 'amazonOffset': 300, 'studio': 'LJC'},
    {'name': 'kenocasino', 'aabOffset': 500, 'amazonOffset': 400, 'studio': 'LJC'},
    {'name': 'kenosuper4x', 'aabOffset': 600, 'amazonOffset': 500, 'studio': 'LJC'},
    {'name': 'roulette', 'aabOffset': 600, 'amazonOffset': 500, 'studio': 'LJC'},
    {'name': 'vintageslots', 'aabOffset': 600, 'amazonOffset': 500, 'studio': 'LJC'},
    {'name': 'videopokercasino', 'aabOffset': 700, 'amazonOffset': 600, 'studio': 'LJC'},
    {'name': 'multihandpoker', 'aabOffset': 700, 'amazonOffset': 600, 'studio': 'LJC'},
    # Free Vegas Games
    {'name': 'fvg-multicardkeno', 'aabOffset': 200, 'amazonOffset': 100, 'studio': 'FVG'},
    {'name': 'fvg-keno', 'aabOffset': 500, 'amazonOffset': 250, 'studio': 'FVG'},
    {'name': 'fvg-fourcardkeno', 'aabOffset': 400, 'amazonOffset': 200, 'studio': 'FVG'}
]

def get_workflow_file(app):
    """Get the workflow filename for an app"""
    workflow_map = {
        'kenocasino': 'keno-builds.yml',
        'blackjack21': 'blackjack-builds.yml',
        'fvg-multicardkeno': 'fvg-multicardkeno-builds.yml',
        'fvg-keno': 'fvg-keno-builds.yml',
        'fvg-fourcardkeno': 'fvg-fourcardkeno-builds.yml'
    }
    return workflow_map.get(app, f'{app}-builds.yml')

def trigger_app_build(app, platform):
    """Trigger a build for an app on a specific platform"""
    try:
        # First check if there are already queued or running builds
        check_cmd = f'{GH_CLI} run list --repo LuckyJackpotCasino/{app} --limit 5 --json status,databaseId 2>&1'
        check_result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if check_result.returncode == 0 and check_result.stdout.strip():
            try:
                runs = json.loads(check_result.stdout)
                queued_or_running = [r for r in runs if r.get('status') in ['queued', 'in_progress', 'waiting']]
                
                if queued_or_running:
                    print(f"⏸️  Skipping trigger for {app} - {len(queued_or_running)} builds already queued/running", flush=True)
                    return {
                        'success': False, 
                        'error': f'{len(queued_or_running)} build(s) already queued/running',
                        'skipped': True
                    }
            except json.JSONDecodeError:
                pass  # If we can't parse, proceed with trigger
        
        workflow = get_workflow_file(app)
        
        # Map platform to build_platforms input
        platform_map = {
            'all': 'ios,aab,amazon,windows',
            'ios': 'ios',
            'aab': 'aab',
            'amazon': 'amazon',
            'windows': 'windows'
        }
        platforms_input = platform_map.get(platform, platform)
        
        cmd = f'{GH_CLI} workflow run {workflow} --repo LuckyJackpotCasino/{app} -f build_platforms="{platforms_input}" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Triggered {app} ({platform})", flush=True)
            # Clear cache for this app so next status check fetches fresh data
            if app in cache:
                del cache[app]
            if app in cache_time:
                del cache_time[app]
            return {'success': True, 'app': app, 'platform': platform}
        else:
            return {'success': False, 'error': result.stderr or result.stdout}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def cancel_app_build(app, run_id):
    """Cancel a running build for an app"""
    try:
        cmd = f'{GH_CLI} run cancel {run_id} --repo LuckyJackpotCasino/{app} 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Clear cache for this app
            if app in cache:
                del cache[app]
            if app in cache_time:
                del cache_time[app]
            return {'success': True, 'app': app, 'run_id': run_id}
        else:
            return {'success': False, 'error': result.stderr or result.stdout}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_local_build_status(app):
    """Check if this app is currently building on any runner"""
    print(f"[LOCAL-CHECK] Checking if {app} is building...", flush=True)
    try:
        # Use runner status to determine if app is actively building
        runner_data = get_runner_status()
        
        for runner in runner_data.get('runners', []):
            if runner.get('busy') and runner.get('project') == app:
                print(f"[LOCAL] ⚡ {app} is BUILDING on {runner.get('name')}", flush=True)
                # App is actively building - mark iOS as in_progress (assume iOS build)
                # TODO: Could check workflow file or job details for actual platform
                return {'ios': 'in_progress'}
        
        print(f"[LOCAL-CHECK] {app} is not currently building on any runner", flush=True)
        return None
    except Exception as e:
        print(f"[LOCAL-CHECK] Error checking local status for {app}: {e}", flush=True)
        return None

def get_build_status(app):
    """Fetch build status for an app from GitHub Actions"""
    global rate_limited_until
    
    # First check local runner status for instant feedback
    local_status = check_local_build_status(app)
    
    # If local shows in_progress, ALWAYS return that immediately (don't use cache)
    if local_status and any(status == 'in_progress' for status in local_status.values()):
        print(f"[OVERRIDE] {app} is building locally - showing in_progress", flush=True)
        # Still fetch from cache for other platforms, but override in_progress ones
        if app in cache:
            cached = cache[app].copy()
            for platform, local_state in local_status.items():
                if local_state == 'in_progress':
                    cached[platform] = 'in_progress'
            return cached
        # No cache, return local status with pending for others
        result = {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending', 'windows': 'pending'}
        result.update(local_status)
        return result
    
    # If rate limited, return stale cache with indicator
    if time.time() < rate_limited_until:
        if app in cache:
            status = cache[app].copy()
            status['rate_limited'] = True
            return status
        return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending', 'windows': 'pending', 'rate_limited': True}
    
    # Smart cache: use cache UNLESS status suggests it might be stale
    if app in cache and app in cache_time:
        cache_age = time.time() - cache_time[app]
        
        # If cache shows "queued" or "in_progress", refresh more frequently (30 sec)
        # If cache shows stable status (success/failure), use full cache duration (5 min)
        cached = cache[app]
        has_unstable_status = any(
            status in ['queued', 'in_progress', 'waiting'] 
            for status in [cached.get('ios'), cached.get('aab'), cached.get('amazon')]
        )
        
        # BUGFIX: If cache shows "in_progress" but nothing is building locally, force immediate refresh
        # This fixes stale "building" status when build already completed/failed/skipped
        if has_unstable_status and not local_status:
            print(f"[CACHE-BUST] {app} shows in_progress in cache but not building locally - forcing refresh", flush=True)
            # Continue to fresh API check below
        else:
            cache_duration = 30 if has_unstable_status else CACHE_DURATION
            
            if cache_age < cache_duration:
                print(f"[CACHE] Using {cache_age:.0f}s old cache for {app} (max: {cache_duration}s)", flush=True)
                return cached.copy()
    
    try:
        # Get recent workflow runs - check MORE runs to find last actual build per platform
        cmd = f"{GH_CLI} run list --repo LuckyJackpotCasino/{app} --limit 25 --json status,conclusion,databaseId,number 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0 or not result.stdout.strip():
            return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending', 'windows': 'pending'}
        
        runs = json.loads(result.stdout)
        status = {
            'ios': 'pending',
            'aab': 'pending',
            'amazon': 'pending',
            'windows': 'pending',
            'iosRun': None,
            'aabRun': None,
            'amazonRun': None,
            'windowsRun': None,
            'iosRunId': None,
            'aabRunId': None,
            'amazonRunId': None,
            'windowsRunId': None
        }
        
        # Track skipped builds as fallback (in case we don't find any non-skipped builds)
        skipped_fallback = {
            'ios': None,
            'aab': None,
            'amazon': None,
            'windows': None
        }
        
        # Check each run's jobs to find the most recent status for EACH platform
        # Prefer non-skipped builds, but fall back to skipped if that's all we have
        # OPTIMIZATION: Stop early if we've found all 3 platforms
        for run in runs[:10]:  # Reduced from 25 to 10 for performance
            run_id = run['databaseId']
            run_number = run.get('number', run_id)  # Use run_number if available, fallback to databaseId
            run_status = run['status']
            
            # Early exit if we've already found all 4 platforms (non-skipped)
            if status['iosRun'] and status['aabRun'] and status['amazonRun'] and status['windowsRun']:
                break
            
            # Get jobs for this run to see which platforms were built
            jobs_cmd = f"{GH_CLI} run view {run_id} --repo LuckyJackpotCasino/{app} --json jobs 2>/dev/null"
            jobs_result = subprocess.run(jobs_cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            if jobs_result.returncode == 0 and jobs_result.stdout.strip():
                try:
                    run_data = json.loads(jobs_result.stdout)
                    jobs = run_data.get('jobs', [])
                    
                    for job in jobs:
                        job_name = job.get('name', '').lower()
                        job_status = job.get('conclusion') if job.get('status') == 'completed' else job.get('status')
                        job_conclusion = job.get('conclusion')
                        
                        # Skip setup jobs
                        if job_name == 'setup':
                            continue
                        
                        # Detect platform from job name
                        platform = None
                        if 'build-ios' in job_name or 'ios' in job_name:
                            platform = 'ios'
                        elif 'build-aab' in job_name or 'aab' in job_name:
                            platform = 'aab'
                        elif 'build-amazon' in job_name or 'amazon' in job_name:
                            platform = 'amazon'
                        elif 'build-windows' in job_name or 'windows' in job_name:
                            platform = 'windows'
                        
                        if not platform:
                            continue
                        
                        # Store as fallback if skipped (only if we don't have a fallback yet)
                        if job_conclusion == 'skipped':
                            if skipped_fallback[platform] is None:
                                skipped_fallback[platform] = {
                                    'status': 'skipped',
                                    'run_number': run_number,
                                    'run_id': run_id
                                }
                            continue
                        
                        # Store actual build status (only if we haven't found one yet for this platform)
                        if status[f'{platform}Run'] is None:
                            status[platform] = job_status or 'unknown'
                            status[f'{platform}Run'] = run_number  # Display number
                            status[f'{platform}RunId'] = run_id    # API ID
                except:
                    pass
        
        # Apply fallbacks for platforms where we found no actual builds
        for platform in ['ios', 'aab', 'amazon', 'windows']:
            if status[f'{platform}Run'] is None and skipped_fallback[platform]:
                fb = skipped_fallback[platform]
                status[platform] = fb['status']
                status[f'{platform}Run'] = fb['run_number']
                status[f'{platform}RunId'] = fb['run_id']
        
        cache[app] = status
        cache_time[app] = time.time()
        
        # Log cache update for debugging
        print(f"[{time.strftime('%H:%M:%S')}] Cached status for {app}", flush=True)
        return status
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error fetching {app}: {error_msg}", flush=True)
        
        # Detect rate limiting
        if 'rate limit' in error_msg.lower() or 'API rate limit exceeded' in error_msg:
            print(f"⚠️  RATE LIMITED! Pausing API calls for 1 hour", flush=True)
            rate_limited_until = time.time() + 3600  # Pause for 1 hour
        
        # Return stale cache if available
        if app in cache:
            return cache[app]
        return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending', 'windows': 'pending'}

def get_runner_status():
    """Fetch status of all GitHub Actions runners from local system"""
    global runner_states
    
    try:
        runners = []
        base_dir = os.path.expanduser('~/actions-runners')
        completed_jobs = []  # Track jobs that just completed
        
        # Look for mac-studio-runner directories
        if not os.path.exists(base_dir):
            return {'error': 'Runners directory not found', 'total': 0, 'online': 0, 'busy': 0, 'idle': 0, 'runners': []}
        
        for item in os.listdir(base_dir):
            if item.startswith('mac-studio-runner'):
                runner_dir = os.path.join(base_dir, item)
                if os.path.isdir(runner_dir):
                    # Check if service is running via svc.sh status
                    try:
                        status_cmd = f"cd {runner_dir} && ./svc.sh status 2>&1"
                        result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True, timeout=5)
                        output = result.stdout.lower()
                        
                        print(f"[RUNNER-DEBUG] {item}: output='{output[:100]}'", flush=True)
                        
                        # Parse status from output
                        is_running = 'started:' in output or 'running' in output
                        
                        print(f"[RUNNER-DEBUG] {item}: is_running={is_running}", flush=True)
                        
                        # Check if busy and get project name
                        is_busy = False
                        project_name = None
                        
                        work_dir = os.path.join(runner_dir, '_work')
                        if os.path.exists(work_dir):
                            # Get the most recent Worker log
                            diag_dir = os.path.join(runner_dir, '_diag')
                            if os.path.exists(diag_dir):
                                worker_logs = [f for f in os.listdir(diag_dir) if f.startswith('Worker_')]
                                if worker_logs:
                                    latest_log = max(worker_logs, key=lambda f: os.path.getmtime(os.path.join(diag_dir, f)))
                                    log_path = os.path.join(diag_dir, latest_log)
                                    # Check if log was modified in last 2 minutes (indicates active job)
                                    mtime = os.path.getmtime(log_path)
                                    if time.time() - mtime < 120:
                                        is_busy = True
                                        
                                        # Try to extract project name from log
                                        try:
                                            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                                # Read last 1000 lines to find job info
                                                lines = f.readlines()[-1000:]
                                                
                                                # Get valid app names
                                                app_names = [app['name'] for app in apps]
                                                
                                                for line in lines:
                                                    # Look for repository info in logs - be more specific
                                                    if 'LuckyJackpotCasino/' in line:
                                                        # Extract repo name from URLs like "LuckyJackpotCasino/kenocasino"
                                                        import re
                                                        # Match only after LuckyJackpotCasino/ and before space, slash, or end
                                                        match = re.search(r'LuckyJackpotCasino/([a-z0-9\-]+)(?:\s|/|$|\.git)', line, re.IGNORECASE)
                                                        if match:
                                                            candidate = match.group(1)
                                                            # Validate it's a real app name from our apps list
                                                            if candidate in app_names:
                                                                project_name = candidate
                                                                print(f"[DEBUG] Found project in log: {project_name}", flush=True)
                                                                break
                                                
                                                # If we found a valid project, stop searching
                                                if project_name:
                                                    break
                                        except Exception as log_err:
                                                            print(f"Error reading log {log_path}: {log_err}", flush=True)
                            
                            # If still no project name, check work directory for repos
                            if is_busy and not project_name:
                                try:
                                    work_items = os.listdir(work_dir)
                                    # Filter out metadata directories
                                    repos = [d for d in work_items if not d.startswith('_') and os.path.isdir(os.path.join(work_dir, d))]
                                    if repos:
                                        # Get most recently modified repo directory
                                        repos_with_mtime = [(d, os.path.getmtime(os.path.join(work_dir, d))) for d in repos]
                                        if repos_with_mtime:
                                            project_name = max(repos_with_mtime, key=lambda x: x[1])[0]
                                except:
                                    pass
                        
                        # Detect job completion: was busy, now idle
                        runner_name = item
                        previous_state = runner_states.get(runner_name, {})
                        
                        if previous_state.get('busy') and not is_busy:
                            # Runner just finished a job!
                            completed_project = previous_state.get('project')
                            if completed_project:
                                completed_jobs.append(completed_project)
                                print(f"🎯 [JOB COMPLETE] {runner_name} just finished building {completed_project}! Clearing cache...", flush=True)
                                # Clear cache for this app to force immediate refresh
                                if completed_project in cache:
                                    del cache[completed_project]
                                if completed_project in cache_time:
                                    del cache_time[completed_project]
                        
                        # Update runner state tracking
                        runner_states[runner_name] = {
                            'busy': is_busy,
                            'project': project_name,
                            'last_check': time.time()
                        }
                        
                        runners.append({
                            'id': hash(item),
                            'name': item,
                            'status': 'online' if is_running else 'offline',
                            'busy': is_busy,
                            'project': project_name,
                            'labels': ['macos', 'self-hosted', 'mac-studio-runner']
                        })
                    except Exception as e:
                        print(f"Error checking {item}: {e}", flush=True)
                        runners.append({
                            'id': hash(item),
                            'name': item,
                            'status': 'unknown',
                            'busy': False,
                            'project': None,
                            'labels': ['macos', 'self-hosted', 'mac-studio-runner']
                        })
        
        # Calculate stats
        total = len(runners)
        online = len([r for r in runners if r['status'] == 'online'])
        busy = len([r for r in runners if r.get('busy') == True])
        idle = online - busy
        
        result = {
            'total': total,
            'online': online,
            'busy': busy,
            'idle': idle,
            'runners': runners,
            'completed_jobs': completed_jobs  # Include list of just-completed jobs
        }
        
        print(f"[RUNNER-RESULT] Returning {total} runners: {online} online, {busy} busy", flush=True)
        
        return result
        
    except Exception as e:
        print(f"Error fetching runner status: {e}", flush=True)
        return {'error': str(e), 'total': 0, 'online': 0, 'busy': 0, 'idle': 0, 'runners': []}

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Serve dashboard HTML
        if parsed_path.path == '/' or parsed_path.path == '/dashboard':
            try:
                with open('dashboard.html', 'r') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(content.encode())
            except FileNotFoundError:
                self.send_error(404, 'Dashboard not found')
            return
        
        # API: Get status for specific app
        if parsed_path.path.startswith('/status/'):
            app_name = parsed_path.path.split('/status/')[1]
            if any(app['name'] == app_name for app in apps):
                status = get_build_status(app_name)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
            else:
                self.send_error(404, 'App not found')
            return
        
        # API: Get status for all apps
        if parsed_path.path in ['/status', '/api/status']:
            results = {}
            for app in apps:
                results[app['name']] = get_build_status(app['name'])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            return
        
        # API: Get runner status
        if parsed_path.path in ['/runners', '/api/runners']:
            runner_status = get_runner_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(json.dumps(runner_status).encode())
            return
        
        # API: Get agent activity (last 20 lines of log)
        if parsed_path.path in ['/agent', '/api/agent']:
            try:
                import subprocess
                result = subprocess.run(
                    ['tail', '-50', '/tmp/buildbot-agent.log'],
                    capture_output=True, text=True, timeout=5
                )
                
                # Check if agent is running
                ps_result = subprocess.run(
                    ['pgrep', '-f', 'python3 build-fix-agent.py'],
                    capture_output=True, text=True, timeout=5
                )
                is_running = ps_result.returncode == 0
                
                agent_data = {
                    'running': is_running,
                    'log': result.stdout if result.returncode == 0 else '',
                    'pid': ps_result.stdout.strip() if is_running else None
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(agent_data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return
        
        self.send_error(404, 'Not found')
    
    def do_POST(self):
        """Handle POST requests for triggering builds"""
        parsed_path = urlparse(self.path)
        
        # Trigger single app build
        if parsed_path.path.startswith('/trigger/'):
            parts = parsed_path.path.split('/')
            if len(parts) >= 4:
                app_name = parts[2]
                platform = parts[3]
                
                if not any(app['name'] == app_name for app in apps):
                    self.send_error(404, 'App not found')
                    return
                
                if platform not in ['all', 'ios', 'aab', 'amazon', 'windows']:
                    self.send_error(400, 'Invalid platform')
                    return
                
                result = trigger_app_build(app_name, platform)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
        
        # Trigger bulk builds
        if parsed_path.path.startswith('/trigger-bulk/'):
            platform = parsed_path.path.split('/trigger-bulk/')[1]
            
            if platform not in ['all', 'ios', 'aab', 'amazon', 'windows']:
                self.send_error(400, 'Invalid platform')
                return
            
            results = []
            successful = []
            
            for app in apps:
                result = trigger_app_build(app['name'], platform)
                results.append(result)
                if result['success']:
                    successful.append(app['name'])
                time.sleep(1)  # Small delay between triggers
            
            response = {
                'success': len(successful) > 0,
                'count': len(successful),
                'apps': successful,
                'results': results
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Cancel build
        if parsed_path.path.startswith('/cancel/'):
            parts = parsed_path.path.split('/')
            if len(parts) >= 4:
                app_name = parts[2]
                run_id = parts[3]
                
                if not any(app['name'] == app_name for app in apps):
                    self.send_error(404, 'App not found')
                    return
                
                result = cancel_app_build(app_name, run_id)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                return
        
        # Restart runner
        if parsed_path.path.startswith('/restart-runner/'):
            runner_id = parsed_path.path.split('/restart-runner/')[1]
            
            try:
                import subprocess
                result = subprocess.run(
                    ['launchctl', 'kickstart', '-k', f'gui/{os.getuid()}/actions.runner.LuckyJackpotCasino.{runner_id}'],
                    capture_output=True, text=True, timeout=10
                )
                
                response = {
                    'success': result.returncode == 0,
                    'runner': runner_id,
                    'message': f'Restarted {runner_id}' if result.returncode == 0 else result.stderr
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            return
        
        self.send_error(404, 'Not found')
    
    def log_message(self, format, *args):
        # Custom logging
        return

if __name__ == '__main__':
    # Allow socket reuse to prevent "Address already in use" errors
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print("""
╔════════════════════════════════════════════════════════════╗
║   🎰 Multi-Studio Build Dashboard Server                  ║
║   Lucky Jackpot Casino + Free Vegas Games                 ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║   Dashboard: http://localhost:8765                         ║
║   API:       http://localhost:8765/api/status              ║
║                                                             ║
║   Press Ctrl+C to stop                                     ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
        """)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard server stopped")
            httpd.shutdown()
