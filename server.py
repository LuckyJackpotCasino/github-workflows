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
        workflow = get_workflow_file(app)
        
        # Map platform to build_platforms input
        platform_map = {
            'all': 'ios,aab,amazon',
            'ios': 'ios',
            'aab': 'aab',
            'amazon': 'amazon'
        }
        platforms_input = platform_map.get(platform, platform)
        
        cmd = f'{GH_CLI} workflow run {workflow} --repo LuckyJackpotCasino/{app} -f build_platforms="{platforms_input}" 2>&1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
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
    """Check local runner work directories for real-time build status"""
    try:
        base_dir = os.path.expanduser('~/actions-runners')
        status_updates = {}
        
        # Check all runners for this app
        for runner_name in os.listdir(base_dir):
            if not runner_name.startswith('mac-studio-runner'):
                continue
                
            runner_dir = os.path.join(base_dir, runner_name)
            work_dir = os.path.join(runner_dir, '_work', app, app)
            
            if not os.path.exists(work_dir):
                continue
            
            # Check if runner is actively building THIS app
            diag_dir = os.path.join(runner_dir, '_diag')
            if os.path.exists(diag_dir):
                worker_logs = [f for f in os.listdir(diag_dir) if f.startswith('Worker_')]
                if worker_logs:
                    latest_log = max(worker_logs, key=lambda f: os.path.getmtime(os.path.join(diag_dir, f)))
                    log_path = os.path.join(diag_dir, latest_log)
                    mtime = os.path.getmtime(log_path)
                    
                    # If worker log modified in last 2 minutes, runner is active
                    if time.time() - mtime < 120:
                        try:
                            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                log_lines = f.readlines()[-500:]  # Check last 500 lines
                                log_content = ''.join(log_lines)
                                
                                # Check if this log mentions our app
                                if app in log_content or f'/{app}/' in log_content:
                                    # This runner is actively working on this app!
                                    # Try to determine which platform
                                    if 'Build-iOS' in log_content or 'unity-ios-build' in log_content:
                                        status_updates['ios'] = 'in_progress'
                                    if 'Build-AAB' in log_content or 'unity-android-build' in log_content:
                                        # Check if it's AAB or Amazon
                                        if 'Build-Amazon' in log_content:
                                            status_updates['amazon'] = 'in_progress'
                                        else:
                                            status_updates['aab'] = 'in_progress'
                        except Exception as e:
                            print(f"Error reading worker log: {e}", flush=True)
            
            # Check for recent Unity log files
            unity_logs = []
            for root, dirs, files in os.walk('/tmp'):
                for f in files:
                    if f.startswith('unity-build-') and f.endswith('.log'):
                        log_path = os.path.join(root, f)
                        try:
                            mtime = os.path.getmtime(log_path)
                            # Only check logs modified in last 30 minutes
                            if time.time() - mtime < 1800:
                                unity_logs.append((log_path, mtime))
                        except:
                            pass
            
            # Check most recent Unity log
            if unity_logs:
                latest_log = max(unity_logs, key=lambda x: x[1])[0]
                try:
                    with open(latest_log, 'r') as f:
                        log_content = f.read()
                        
                        # Check for build completion indicators
                        if 'Build completed successfully' in log_content or 'Build succeeded' in log_content:
                            # Determine platform from log
                            if 'BuildiOS' in log_content or 'iOS' in log_content:
                                status_updates['ios'] = 'success'
                            elif 'BuildGooglePlay' in log_content or 'AAB' in log_content:
                                status_updates['aab'] = 'success'
                            elif 'BuildAmazon' in log_content or 'APK' in log_content:
                                status_updates['amazon'] = 'success'
                        
                        # Check for build failures
                        elif 'Build failed' in log_content or 'Error building Player' in log_content:
                            if 'BuildiOS' in log_content or 'iOS' in log_content:
                                status_updates['ios'] = 'failure'
                            elif 'BuildGooglePlay' in log_content:
                                status_updates['aab'] = 'failure'
                            elif 'BuildAmazon' in log_content:
                                status_updates['amazon'] = 'failure'
                        
                        # Check for builds in progress
                        elif 'Starting Unity' in log_content or 'Building Player' in log_content:
                            # Check file modification time - if modified in last 2 minutes, it's active
                            mtime = os.path.getmtime(latest_log)
                            if time.time() - mtime < 120:
                                if 'BuildiOS' in log_content or 'iOS' in log_content:
                                    status_updates['ios'] = 'in_progress'
                                elif 'BuildGooglePlay' in log_content:
                                    status_updates['aab'] = 'in_progress'
                                elif 'BuildAmazon' in log_content:
                                    status_updates['amazon'] = 'in_progress'
                except Exception as e:
                    print(f"Error reading Unity log {latest_log}: {e}", flush=True)
            
            # Check for output artifacts (definitive proof of success)
            ios_project = os.path.join(work_dir, 'IosProjectFolder')
            if os.path.exists(ios_project):
                # Check if modified recently (last 30 min)
                mtime = os.path.getmtime(ios_project)
                if time.time() - mtime < 1800:
                    # Only mark as success if not currently building
                    if 'ios' not in status_updates or status_updates['ios'] != 'in_progress':
                        status_updates['ios'] = 'success'
            
            # Check for Android builds
            for ext in ['*.aab', '*.apk']:
                import glob
                artifacts = glob.glob(os.path.join(work_dir, ext))
                for artifact in artifacts:
                    mtime = os.path.getmtime(artifact)
                    if time.time() - mtime < 1800:
                        if ext == '*.aab':
                            if 'aab' not in status_updates or status_updates['aab'] != 'in_progress':
                                status_updates['aab'] = 'success'
                        elif ext == '*.apk':
                            if 'amazon' not in status_updates or status_updates['amazon'] != 'in_progress':
                                status_updates['amazon'] = 'success'
        
        return status_updates if status_updates else None
        
    except Exception as e:
        print(f"Error checking local build status for {app}: {e}", flush=True)
        return None

def get_build_status(app):
    """Fetch build status for an app from GitHub Actions"""
    global rate_limited_until
    
    # First check local runner status for instant feedback
    local_status = check_local_build_status(app)
    
    # If rate limited, return stale cache with indicator
    if time.time() < rate_limited_until:
        if app in cache:
            status = cache[app].copy()
            status['rate_limited'] = True
            # Merge local status if available - local status overrides stale cache
            if local_status:
                for platform, local_state in local_status.items():
                    if local_state == 'in_progress':
                        # Currently building - override old status
                        status[platform] = 'in_progress'
                    elif local_state in ['success', 'failure']:
                        # New completion status
                        status[platform] = local_state
            return status
        return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending', 'rate_limited': True}
    
    # Return cache if less than CACHE_DURATION old, but merge local status
    if app in cache and app in cache_time:
        if time.time() - cache_time[app] < CACHE_DURATION:
            cached = cache[app].copy()
            if local_status:
                # Local status takes FULL precedence - if building now, override old status
                for platform, local_state in local_status.items():
                    if local_state == 'in_progress':
                        # If currently building, always show in_progress (not old success/failure)
                        cached[platform] = 'in_progress'
                    elif local_state in ['success', 'failure']:
                        # Update with new completion status
                        cached[platform] = local_state
            return cached
    
    try:
        # Get recent workflow runs (gh CLI uses authenticated token automatically)
        cmd = f"{GH_CLI} run list --repo LuckyJackpotCasino/{app} --limit 3 --json status,conclusion,databaseId 2>/dev/null"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0 or not result.stdout.strip():
            return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending'}
        
        runs = json.loads(result.stdout)
        status = {
            'ios': 'pending',
            'aab': 'pending',
            'amazon': 'pending',
            'iosRun': None,
            'aabRun': None,
            'amazonRun': None
        }
        
        # Check each run's jobs to determine what platform was built
        for run in runs[:3]:  # Check last 3 runs
            run_id = run['databaseId']
            
            # Get jobs for this run to see which platforms were built
            jobs_cmd = f"{GH_CLI} run view {run_id} --repo LuckyJackpotCasino/{app} --json jobs 2>/dev/null"
            jobs_result = subprocess.run(jobs_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if jobs_result.returncode == 0 and jobs_result.stdout.strip():
                try:
                    run_data = json.loads(jobs_result.stdout)
                    jobs = run_data.get('jobs', [])
                    
                    for job in jobs:
                        job_name = job.get('name', '').lower()
                        job_status = job.get('conclusion') if job.get('status') == 'completed' else job.get('status')
                        
                        # Skip setup jobs
                        if job_name == 'setup':
                            continue
                        
                        # Detect platform from job name (handle "build-ios / build" format)
                        if ('build-ios' in job_name or 'ios' in job_name) and status['iosRun'] is None:
                            status['ios'] = job_status or 'unknown'
                            status['iosRun'] = run_id
                        elif ('build-aab' in job_name or 'aab' in job_name) and status['aabRun'] is None:
                            status['aab'] = job_status or 'unknown'
                            status['aabRun'] = run_id
                        elif ('build-amazon' in job_name or 'amazon' in job_name) and status['amazonRun'] is None:
                            status['amazon'] = job_status or 'unknown'
                            status['amazonRun'] = run_id
                except:
                    pass
        
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
        return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending'}

def get_runner_status():
    """Fetch status of all GitHub Actions runners from local system"""
    try:
        runners = []
        base_dir = os.path.expanduser('~/actions-runners')
        
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
                        
                        # Parse status from output
                        is_running = 'started:' in output or 'running' in output
                        
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
                                                for line in lines:
                                                    # Look for repository info in logs
                                                    if 'luckyjackpotcasino' in line.lower():
                                                        # Extract repo name from URLs like "LuckyJackpotCasino/kenocasino"
                                                        import re
                                                        match = re.search(r'LuckyJackpotCasino/([a-zA-Z0-9_-]+)', line, re.IGNORECASE)
                                                        if match:
                                                            project_name = match.group(1)
                                                            print(f"[DEBUG] Found project in log: {project_name}", flush=True)
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
        
        return {
            'total': total,
            'online': online,
            'busy': busy,
            'idle': idle,
            'runners': runners
        }
        
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
            self.end_headers()
            self.wfile.write(json.dumps(results).encode())
            return
        
        # API: Get runner status
        if parsed_path.path in ['/runners', '/api/runners']:
            runner_status = get_runner_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(runner_status).encode())
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
                
                if platform not in ['all', 'ios', 'aab', 'amazon']:
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
            
            if platform not in ['all', 'ios', 'aab', 'amazon']:
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
