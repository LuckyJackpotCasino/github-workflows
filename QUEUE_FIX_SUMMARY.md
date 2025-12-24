# BuildBot9000 Queue Management Fix

## Problem
The auto-fix agent was triggering multiple rebuild attempts, causing a queue of duplicate builds (21 queued builds for videopokercasino).

## Root Cause
1. Agent didn't check if builds were already queued before triggering
2. Dashboard's trigger buttons didn't check for existing queued builds
3. No visibility into how many builds were queued

## Solutions Implemented

### 1. Server-Side Queue Check (`server.py`)
**Function: `trigger_app_build()`**

```python
# Check for existing queued/running builds BEFORE triggering
check_cmd = f'{GH_CLI} run list --repo LuckyJackpotCasino/{app} --limit 5 --json status,databaseId'
runs = json.loads(result.stdout)
queued_or_running = [r for r in runs if r.get('status') in ['queued', 'in_progress', 'waiting']]

if queued_or_running:
    return {'success': False, 'error': f'{len(queued_or_running)} build(s) already queued/running', 'skipped': True}
```

**Result:** ✅ No duplicate builds triggered from dashboard

### 2. Agent Queue Check (`build-fix-agent.py`)
**Function: `check_app_failures()`**

```python
# Check if there are any queued or in_progress builds
runs = json.loads(result.stdout)
pending_runs = [r for r in runs if r['status'] in ['queued', 'in_progress', 'waiting']]

if pending_runs:
    print(f"⏸️  Skipping {app} - {len(pending_runs)} builds already queued/running")
    return  # Don't trigger more builds
```

**Result:** ✅ Agent won't pile on more builds

### 3. Dashboard UI Feedback (`dashboard.html`)

```javascript
if (result.success) {
    btn.textContent = '✅';
} else if (result.skipped) {
    btn.textContent = '⏸️ Queued';  // Shows when build already queued
} else {
    btn.textContent = '❌';
}
```

**Result:** ✅ User sees when builds are skipped due to queue

### 4. Runner Project Detection Fix (`server.py`)

Fixed regex to avoid false positives like "repos", "followrs":

```python
# Match only valid app names, exclude path components
match = re.search(r'LuckyJackpotCasino/([a-z0-9\-]+)(?:\s|/|$|\.git)', line)
if match:
    candidate = match.group(1)
    if candidate not in ['repos', 'actions', '.git', 'workflows']:
        project_name = candidate
```

**Result:** ✅ Runner cards show correct project names (not "repos" or "followrs")

## Usage

### Dashboard
- **Try to trigger a build**: If already queued, button shows "⏸️ Queued"
- **No duplicate triggers**: System prevents queue buildup

### Auto-Fix Agent
```bash
# Start agent (now queue-aware)
cd /Users/ci/Documents/BuildBot9000/github-workflows
./start-fix-agent.sh

# Agent will now log:
# ⏸️  Skipping videopokercasino - 4 builds already queued/running
```

### Checking Queue Status
```bash
# Via GitHub CLI
gh run list --repo LuckyJackpotCasino/videopokercasino --limit 10

# See queued count in dashboard
# Look at runner section - shows what's building
```

## Before vs After

**Before:**
- ❌ Agent triggers rebuild on every check (every 30s)
- ❌ 21 queued builds pile up
- ❌ No indication of queue depth
- ❌ Runners show "Building repos" (wrong)

**After:**
- ✅ Agent checks queue first, skips if builds pending
- ✅ Dashboard prevents duplicate triggers
- ✅ UI shows "⏸️ Queued" feedback
- ✅ Runners show actual project names

## Preventing Future Queue Buildup

1. **Agent stays disabled by default** - Only run when needed
2. **Manual trigger checks queue** - Safe to use dashboard
3. **Monitor with**: `gh run list --repo LuckyJackpotCasino/APP --limit 10`
4. **Cancel excess**: Use dashboard cancel buttons (✖)

## Next Steps

If you want to re-enable the agent with these safeguards:

```bash
cd /Users/ci/Documents/BuildBot9000/github-workflows
./start-fix-agent.sh
tail -f /tmp/buildbot-agent.log
```

The agent will now be much more conservative and won't create queue pile-ups!

