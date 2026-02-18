#!/usr/bin/env python3
"""
BuildBot9000 Auto-Fix Agent
Monitors failed builds and automatically applies fixes for common issues.
"""

import subprocess
import time
import re
import os
import json
from datetime import datetime

GH_CLI = '/opt/homebrew/bin/gh'

# Track which failures we've already attempted to fix
attempted_fixes = {}

class BuildFailureAnalyzer:
    """Analyzes build failures and determines appropriate fixes"""
    
    def __init__(self, app_name, run_id, job_name):
        self.app = app_name
        self.run_id = run_id
        self.job_name = job_name
        self.logs = None
        self.fix_applied = None
        
    def fetch_logs(self):
        """Fetch job logs from GitHub Actions"""
        try:
            cmd = f"{GH_CLI} run view {self.run_id} --repo LuckyJackpotCasino/{self.app} --log"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.logs = result.stdout
                return True
            return False
        except Exception as e:
            print(f"❌ Error fetching logs: {e}", flush=True)
            return False
    
    def analyze_and_fix(self):
        """Analyze failure and apply fix if possible"""
        if not self.logs:
            return None
        
        # Pattern matching for common failures
        fixes = [
            self._fix_cocoapods_duplicate_repos,
            self._fix_xcode_command_line_tools,
            self._fix_provisioning_profile_not_found,
            self._fix_keychain_timeout,
            self._fix_unity_terminated,
            self._fix_pod_install_failure,
            self._fix_git_authentication,
            self._fix_certificate_not_found,
            self._fix_transient_network_error,
            self._fix_windows_unity_not_found,
            self._fix_windows_il2cpp_failure,
            self._fix_windows_visual_studio_missing,
            self._fix_windows_disk_space,
        ]
        
        for fix_func in fixes:
            result = fix_func()
            if result:
                self.fix_applied = result
                return result
        
        return None
    
    def _fix_cocoapods_duplicate_repos(self):
        """Fix: CocoaPods duplicate repos causing conflicts"""
        if 'duplicate sources' in self.logs.lower() or 'cocoapods/repos/cocoapods' in self.logs.lower():
            print(f"🔧 Detected: CocoaPods duplicate repos issue", flush=True)
            
            # Clean up duplicate repos
            home = os.path.expanduser('~')
            cocoapods_dir = os.path.join(home, '.cocoapods/repos/cocoapods')
            if os.path.exists(cocoapods_dir):
                try:
                    import shutil
                    shutil.rmtree(cocoapods_dir)
                    print(f"✅ Removed duplicate CocoaPods repo", flush=True)
                    return {
                        'issue': 'CocoaPods duplicate repos',
                        'action': 'Removed ~/. cocoapods/repos/cocoapods',
                        'retry': True
                    }
                except Exception as e:
                    print(f"❌ Failed to remove duplicate repo: {e}", flush=True)
        return None
    
    def _fix_xcode_command_line_tools(self):
        """Fix: xcode-select pointing to Command Line Tools instead of Xcode.app"""
        if 'requires Xcode, but active developer directory' in self.logs and 'CommandLineTools' in self.logs:
            print(f"🔧 Detected: DEVELOPER_DIR not set correctly", flush=True)
            # This should be fixed in workflow now, but log it
            return {
                'issue': 'DEVELOPER_DIR pointing to CommandLineTools',
                'action': 'Already fixed in workflow (DEVELOPER_DIR set at job level)',
                'retry': True,
                'workflow_update_needed': False
            }
        return None
    
    def _fix_provisioning_profile_not_found(self):
        """Fix: Provisioning profile path incorrect"""
        if 'No provisioning profile found after match' in self.logs:
            print(f"🔧 Detected: Provisioning profile path issue", flush=True)
            # This should be fixed in workflow, but could be a Match/Fastlane issue
            return {
                'issue': 'Provisioning profile not found',
                'action': 'Check Fastlane Match configuration',
                'retry': True,
                'investigation_needed': True
            }
        return None
    
    def _fix_keychain_timeout(self):
        """Fix: Keychain locked or timed out"""
        if 'keychain' in self.logs.lower() and ('locked' in self.logs.lower() or 'timeout' in self.logs.lower()):
            print(f"🔧 Detected: Keychain timeout/lock issue", flush=True)
            # Clean up stale keychains
            try:
                result = subprocess.run(
                    "security list-keychains | grep ci-signing | xargs -I {} security delete-keychain {} || true",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                print(f"✅ Cleaned up stale CI keychains", flush=True)
                return {
                    'issue': 'Keychain locked/timeout',
                    'action': 'Cleaned up stale keychains',
                    'retry': True
                }
            except Exception as e:
                print(f"❌ Failed to clean keychains: {e}", flush=True)
        return None
    
    def _fix_unity_terminated(self):
        """Fix: Unity terminated (exit code 143 - SIGTERM)"""
        if 'Terminated: 15' in self.logs or 'exit code 143' in self.logs:
            print(f"🔧 Detected: Unity process terminated", flush=True)
            # Check if there are other Unity processes running
            try:
                result = subprocess.run(
                    "ps aux | grep -i unity | grep -v grep | wc -l",
                    shell=True, capture_output=True, text=True, timeout=5
                )
                unity_count = int(result.stdout.strip())
                
                if unity_count > 2:  # More than expected
                    print(f"⚠️  Warning: {unity_count} Unity processes running - may cause conflicts", flush=True)
                    return {
                        'issue': 'Unity terminated (possible conflict)',
                        'action': 'Multiple Unity instances detected',
                        'retry': True,
                        'note': f'{unity_count} Unity processes running'
                    }
                else:
                    return {
                        'issue': 'Unity terminated (transient)',
                        'action': 'No obvious cause - safe to retry',
                        'retry': True
                    }
            except:
                pass
        return None
    
    def _fix_pod_install_failure(self):
        """Fix: CocoaPods install failure"""
        if 'pod install' in self.logs.lower() and ('error' in self.logs.lower() or 'failed' in self.logs.lower()):
            # Check for specific pod issues
            if 'cdn.cocoapods.org' in self.logs:
                print(f"🔧 Detected: CocoaPods CDN network issue", flush=True)
                return {
                    'issue': 'CocoaPods CDN network error',
                    'action': 'Transient network issue',
                    'retry': True,
                    'delay': 60  # Wait 1 minute before retry
                }
        return None
    
    def _fix_git_authentication(self):
        """Fix: Git authentication failure"""
        if 'Permission denied (publickey)' in self.logs or 'Authentication failed' in self.logs:
            print(f"🔧 Detected: Git authentication failure", flush=True)
            # Check SSH key configuration
            try:
                result = subprocess.run(
                    "ssh -T git@github.com 2>&1",
                    shell=True, capture_output=True, text=True, timeout=10
                )
                if 'successfully authenticated' in result.stdout or 'successfully authenticated' in result.stderr:
                    return {
                        'issue': 'Git authentication (transient)',
                        'action': 'SSH key is valid - retry',
                        'retry': True
                    }
                else:
                    return {
                        'issue': 'Git SSH key invalid',
                        'action': 'SSH key verification failed',
                        'retry': False,
                        'manual_intervention_needed': True
                    }
            except:
                pass
        return None
    
    def _fix_certificate_not_found(self):
        """Fix: Code signing certificate not found"""
        if 'no local code signing identities' in self.logs.lower() or 'certificate' in self.logs.lower() and 'not found' in self.logs.lower():
            print(f"🔧 Detected: Certificate installation issue", flush=True)
            return {
                'issue': 'Code signing certificate not found',
                'action': 'Fastlane Match may need to re-sync',
                'retry': True,
                'note': 'Certificate may not have been installed to keychain properly'
            }
        return None
    
    def _fix_transient_network_error(self):
        """Fix: Transient network errors"""
        network_errors = [
            'connection refused',
            'connection timeout',
            'network is unreachable',
            'temporary failure in name resolution',
            'could not resolve host'
        ]
        
        for error in network_errors:
            if error in self.logs.lower():
                print(f"🔧 Detected: Transient network error", flush=True)
                return {
                    'issue': 'Transient network error',
                    'action': 'Network connectivity issue',
                    'retry': True,
                    'delay': 30
                }
        return None


    def _fix_windows_unity_not_found(self):
        """Fix: Unity not found on Windows runner"""
        if 'no unity installation found' in self.logs.lower() or 'unity.exe' in self.logs.lower() and 'not found' in self.logs.lower():
            print(f"🔧 Detected: Unity not installed on Windows runner", flush=True)
            return {
                'issue': 'Unity not found on Windows runner',
                'action': 'Install Unity via Hub on the Windows build server',
                'retry': False,
                'manual_intervention_needed': True
            }
        return None

    def _fix_windows_il2cpp_failure(self):
        """Fix: IL2CPP build failure on Windows (missing Visual Studio C++ components)"""
        il2cpp_errors = [
            'il2cpp error',
            'il2cpp.exe did not run properly',
            'buildFailedException: il2cpp',
            'c++ compiler not found',
            'msvc',
        ]
        for error in il2cpp_errors:
            if error in self.logs.lower():
                print(f"🔧 Detected: IL2CPP build failure on Windows", flush=True)
                return {
                    'issue': 'IL2CPP build failure (Windows)',
                    'action': 'Verify Visual Studio Build Tools with C++ workload are installed on Windows runner',
                    'retry': True,
                    'note': 'IL2CPP requires Visual Studio with "Desktop development with C++" workload'
                }
        return None

    def _fix_windows_visual_studio_missing(self):
        """Fix: Visual Studio or Build Tools not found"""
        if 'visual studio' in self.logs.lower() and ('not found' in self.logs.lower() or 'not installed' in self.logs.lower()):
            print(f"🔧 Detected: Visual Studio not found on Windows runner", flush=True)
            return {
                'issue': 'Visual Studio Build Tools missing',
                'action': 'Install Visual Studio Build Tools with C++ workload on Windows runner',
                'retry': False,
                'manual_intervention_needed': True
            }
        return None

    def _fix_windows_disk_space(self):
        """Fix: Disk space issues on Windows runner"""
        if 'not enough space' in self.logs.lower() or 'disk full' in self.logs.lower() or 'no space left' in self.logs.lower():
            print(f"🔧 Detected: Disk space issue on Windows runner", flush=True)
            return {
                'issue': 'Windows runner disk space low',
                'action': 'Clean old builds from C:\\Builds and Unity Library cache',
                'retry': True,
                'note': 'Consider running disk cleanup on the Windows build server'
            }
        return None


def monitor_and_fix_failures():
    """Main monitoring loop"""
    print(f"🤖 BuildBot9000 Auto-Fix Agent started at {datetime.now()}", flush=True)
    print(f"Monitoring for failed builds...\n", flush=True)
    
    while True:
        try:
            # Get list of recent workflow runs across all apps
            apps = [
                'blackjack21', 'keno4card', 'keno20card', 'kenocasino', 'kenosuper4x',
                'roulette', 'vintageslots', 'videopokercasino', 'multihandpoker',
                'fvg-multicardkeno', 'fvg-keno', 'fvg-fourcardkeno'
            ]
            
            for app in apps:
                check_app_failures(app)
            
            # Sleep for 30 seconds before next check
            time.sleep(30)
            
        except KeyboardInterrupt:
            print(f"\n🛑 Agent stopped by user", flush=True)
            break
        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}", flush=True)
            time.sleep(30)


def check_app_failures(app):
    """Check for failures in a specific app"""
    global attempted_fixes
    
    try:
        # First, check if there are any queued or in_progress builds
        cmd = f"{GH_CLI} run list --repo LuckyJackpotCasino/{app} --limit 5 --json status,conclusion,databaseId,createdAt"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return
        
        runs = json.loads(result.stdout)
        
        # Check if there are any queued or in_progress runs
        pending_runs = [r for r in runs if r['status'] in ['queued', 'in_progress', 'waiting']]
        if pending_runs:
            print(f"⏸️  Skipping {app} - {len(pending_runs)} builds already queued/running", flush=True)
            return  # Don't analyze failures if builds are already running
        
        for run in runs:
            run_id = run['databaseId']
            status = run['status']
            conclusion = run.get('conclusion')
            
            # Check if this is a completed failure
            if status == 'completed' and conclusion == 'failure':
                # Have we already tried to fix this?
                fix_key = f"{app}:{run_id}"
                if fix_key in attempted_fixes:
                    continue  # Already attempted
                
                print(f"\n🔍 Analyzing failure: {app} (run #{run_id})", flush=True)
                
                # Get job details
                jobs_cmd = f"{GH_CLI} run view {run_id} --repo LuckyJackpotCasino/{app} --json jobs"
                jobs_result = subprocess.run(jobs_cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                if jobs_result.returncode == 0:
                    run_data = json.loads(jobs_result.stdout)
                    jobs = run_data.get('jobs', [])
                    
                    for job in jobs:
                        if job.get('conclusion') == 'failure':
                            job_name = job.get('name', 'unknown')
                            
                            # Analyze and fix
                            analyzer = BuildFailureAnalyzer(app, run_id, job_name)
                            if analyzer.fetch_logs():
                                fix_result = analyzer.analyze_and_fix()
                                
                                if fix_result:
                                    print(f"✅ Fix applied: {fix_result['issue']}", flush=True)
                                    print(f"   Action: {fix_result['action']}", flush=True)
                                    
                                    # Mark as attempted
                                    attempted_fixes[fix_key] = {
                                        'timestamp': time.time(),
                                        'fix': fix_result
                                    }
                                    
                                    # Trigger retry if recommended
                                    if fix_result.get('retry'):
                                        delay = fix_result.get('delay', 0)
                                        if delay > 0:
                                            print(f"⏳ Waiting {delay}s before retry...", flush=True)
                                            time.sleep(delay)
                                        
                                        print(f"🔄 Triggering rebuild for {app}...", flush=True)
                                        trigger_rebuild(app)
                                else:
                                    print(f"❓ No automatic fix available for this failure", flush=True)
                                    # Mark as seen but not fixed
                                    attempted_fixes[fix_key] = {
                                        'timestamp': time.time(),
                                        'fix': None
                                    }
    except Exception as e:
        print(f"Error checking {app}: {e}", flush=True)


def trigger_rebuild(app):
    """Trigger a rebuild for an app"""
    try:
        workflow_map = {
            'kenocasino': 'keno-builds.yml',
            'blackjack21': 'blackjack-builds.yml',
            'fvg-multicardkeno': 'fvg-multicardkeno-builds.yml',
            'fvg-keno': 'fvg-keno-builds.yml',
            'fvg-fourcardkeno': 'fvg-fourcardkeno-builds.yml'
        }
        workflow = workflow_map.get(app, f'{app}-builds.yml')
        
        cmd = f'{GH_CLI} workflow run {workflow} --repo LuckyJackpotCasino/{app} -f build_platforms="ios"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ Rebuild triggered successfully", flush=True)
            return True
        else:
            print(f"❌ Failed to trigger rebuild: {result.stderr}", flush=True)
            return False
    except Exception as e:
        print(f"❌ Error triggering rebuild: {e}", flush=True)
        return False


if __name__ == '__main__':
    monitor_and_fix_failures()

