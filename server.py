#!/usr/bin/env python3

import http.server
import socketserver
import json
import subprocess
import threading
import time
from urllib.parse import urlparse
from datetime import datetime

PORT = 3000

# Cache for build status
cache = {}
cache_time = {}

apps = [
    {'name': 'blackjack21', 'aabOffset': 200, 'amazonOffset': 100},
    {'name': 'keno4card', 'aabOffset': 300, 'amazonOffset': 200},
    {'name': 'keno20card', 'aabOffset': 400, 'amazonOffset': 300},
    {'name': 'kenocasino', 'aabOffset': 500, 'amazonOffset': 400},
    {'name': 'kenosuper4x', 'aabOffset': 600, 'amazonOffset': 500},
    {'name': 'roulette', 'aabOffset': 600, 'amazonOffset': 500},
    {'name': 'vintageslots', 'aabOffset': 600, 'amazonOffset': 500},
    {'name': 'videopokercasino', 'aabOffset': 700, 'amazonOffset': 600},
    {'name': 'multihandpoker', 'aabOffset': 700, 'amazonOffset': 600}
]

def get_workflow_file(app):
    """Get the workflow filename for an app"""
    workflow_map = {
        'kenocasino': 'keno-builds.yml',
        'blackjack21': 'blackjack-builds.yml'
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
        
        cmd = f'gh workflow run {workflow} --repo LuckyJackpotCasino/{app} -f build_platforms="{platforms_input}" 2>&1'
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

def get_build_status(app):
    """Fetch build status for an app from GitHub Actions"""
    # Return cache if less than 30 seconds old
    if app in cache and app in cache_time:
        if time.time() - cache_time[app] < 30:
            return cache[app]
    
    try:
        # Get recent workflow runs
        cmd = f"gh run list --repo LuckyJackpotCasino/{app} --limit 3 --json status,conclusion,databaseId 2>/dev/null"
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
            jobs_cmd = f"gh run view {run_id} --repo LuckyJackpotCasino/{app} --json jobs 2>/dev/null"
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
        return status
        
    except Exception as e:
        print(f"Error fetching {app}: {e}")
        return {'ios': 'pending', 'aab': 'pending', 'amazon': 'pending'}

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
        
        self.send_error(404, 'Not found')
    
    def log_message(self, format, *args):
        # Custom logging
        return

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print("""
╔═══════════════════════════════════════════════════════════╗
║   🎰 Lucky Jackpot Casino - Build Dashboard Server       ║
╠═══════════════════════════════════════════════════════════╣
║                                                            ║
║   Dashboard: http://localhost:3000                        ║
║   API:       http://localhost:3000/api/status             ║
║                                                            ║
║   Press Ctrl+C to stop                                    ║
║                                                            ║
╚═══════════════════════════════════════════════════════════╝
        """)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard server stopped")
            httpd.shutdown()
