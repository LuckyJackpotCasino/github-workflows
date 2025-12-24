# BuildBot9000 Auto-Fix Agent 🤖

An intelligent agent that monitors GitHub Actions build failures and automatically applies fixes for common issues.

## Features

### Automatic Detection & Fixes

The agent monitors all build failures and can automatically fix:

1. **CocoaPods Issues**
   - Duplicate repos causing conflicts
   - CDN network errors (with retry)

2. **Xcode Configuration**
   - `DEVELOPER_DIR` pointing to CommandLineTools instead of Xcode.app
   - Certificate/keychain installation issues

3. **Unity Build Issues**
   - Terminated processes (exit code 143)
   - Multiple Unity instance conflicts

4. **Network Errors**
   - Transient DNS failures
   - Connection timeouts
   - CDN unavailability

5. **Authentication**
   - Git SSH key issues
   - Provisioning profile path problems

6. **Keychain Management**
   - Locked/timed out keychains
   - Stale keychain cleanup

## How It Works

1. **Monitor** - Checks for failed builds every 30 seconds
2. **Analyze** - Fetches logs and pattern-matches against known issues
3. **Fix** - Applies appropriate fix (cleanup, config change, etc.)
4. **Retry** - Automatically triggers rebuild if fix was successful
5. **Track** - Prevents infinite retry loops by tracking attempted fixes

## Usage

### Start the Agent

```bash
cd /Users/ci/Documents/BuildBot9000/github-workflows
./start-fix-agent.sh
```

### View Logs

```bash
# Real-time logs
tail -f /tmp/buildbot-agent.log

# Recent activity
tail -50 /tmp/buildbot-agent.log
```

### Stop the Agent

```bash
pkill -f "python3 build-fix-agent.py"
```

## Agent Output

The agent provides clear status updates:

```
🤖 BuildBot9000 Auto-Fix Agent started at 2025-12-23 14:30:00
Monitoring for failed builds...

🔍 Analyzing failure: videopokercasino (run #12345)
🔧 Detected: CocoaPods duplicate repos issue
✅ Fix applied: CocoaPods duplicate repos
   Action: Removed ~/.cocoapods/repos/cocoapods
🔄 Triggering rebuild for videopokercasino...
✅ Rebuild triggered successfully
```

## Adding New Fixes

To add a new auto-fix pattern, edit `build-fix-agent.py`:

1. Add a new method to `BuildFailureAnalyzer`:

```python
def _fix_your_issue(self):
    """Fix: Description of issue"""
    if 'error pattern' in self.logs.lower():
        print(f"🔧 Detected: Your issue", flush=True)
        
        # Apply fix here
        # ...
        
        return {
            'issue': 'Issue name',
            'action': 'What was done',
            'retry': True,  # Should we retry the build?
            'delay': 30  # Optional: seconds to wait before retry
        }
    return None
```

2. Add it to the `fixes` list in `analyze_and_fix()`:

```python
fixes = [
    # ... existing fixes ...
    self._fix_your_issue,
]
```

## Safety Features

- **No infinite loops** - Each failure is only auto-fixed once
- **Configurable delays** - Network issues wait before retry
- **Manual intervention flagging** - Some issues are logged but not auto-fixed
- **Comprehensive logging** - All actions are logged to `/tmp/buildbot-agent.log`

## Integration with Dashboard

The agent works seamlessly with the build dashboard:
- Dashboard shows build status in real-time
- Agent detects failures from completed jobs
- Automatic rebuilds appear on dashboard immediately
- Users see "Building" → "Failed" → "Building" (auto-retry) → "Success"

## Running at Startup

To run the agent automatically on boot, create a LaunchAgent:

```bash
# Create plist (example provided in setup docs)
~/Library/LaunchAgents/com.buildbot.fix-agent.plist
```

## Monitoring Agent Health

Check if agent is running:

```bash
ps aux | grep build-fix-agent
```

Check recent activity:

```bash
tail -20 /tmp/buildbot-agent.log
```

## Future Enhancements

Potential additions:
- Slack/email notifications when manual intervention needed
- Learning from patterns (ML-based failure prediction)
- Integration with Cursor AI for complex fixes
- Automatic dependency updates when builds fail due to outdated packages
- Performance optimization suggestions

