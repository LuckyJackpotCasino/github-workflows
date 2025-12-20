# Secondary Runner - Quick Reference

## ✅ Setup Complete!

**Runner Name:** MacBook-Pro-Secondary  
**Labels:** `self-hosted`, `macos-secondary`  
**Location:** `~/actions-runners/runner-secondary`  
**Status:** Registered (not running)

---

## 🚀 Starting the Secondary Runner

### Option 1: Run Manually (Recommended)
Run in foreground - you can see all build activity and stop with Ctrl+C:

```bash
cd ~/actions-runners/runner-secondary
./run.sh
```

**When to use:** When you want the runner active for a specific session.

### Option 2: Run as Background Service (Auto-start)
Install as a service that starts automatically on login:

```bash
cd ~/actions-runners/runner-secondary
sudo ./svc.sh install
sudo ./svc.sh start
```

**When to use:** If you want the runner always available.

---

## 🎯 Using the Secondary Runner

### Default Behavior (No Changes Needed)
All existing workflows continue using the **primary runner** automatically.

### Trigger Build on Secondary Runner

**Via GitHub Actions Web UI:**
1. Go to: https://github.com/LuckyJackpotCasino/fvg-multicardkeno/actions
2. Select workflow → "Run workflow"
3. Keep `build_platforms` as desired (e.g., "ios")
4. Set `runner_label` to: **`macos-secondary`**
5. Click "Run workflow"

**Via GitHub CLI:**
```bash
# iOS build on secondary runner
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="ios" \
  -f runner_label="macos-secondary"

# All platforms on secondary runner
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="aab,amazon,ios" \
  -f runner_label="macos-secondary"
```

**Via Dashboard:**
The dashboard doesn't have runner selection yet, but you can add a button if needed!

---

## 🛑 Stopping the Secondary Runner

### If Running Manually:
```bash
# Press Ctrl+C in the terminal running ./run.sh
```

### If Running as Service:
```bash
cd ~/actions-runners/runner-secondary
sudo ./svc.sh stop
```

---

## 🔍 Check Runner Status

### View on GitHub:
https://github.com/organizations/LuckyJackpotCasino/settings/actions/runners

### Check Service Status (if installed as service):
```bash
cd ~/actions-runners/runner-secondary
sudo ./svc.sh status
```

---

## 📊 Current Setup

| Runner | Status | Labels | Usage |
|--------|--------|--------|-------|
| **Primary** | Always On | `self-hosted` | Default (automatic) |
| **Secondary** | Manual | `self-hosted`, `macos-secondary` | On-demand only |

---

## 🎮 Use Cases

✅ **When to use secondary runner:**
- Testing new Unity versions
- Debugging build issues
- Running experimental builds
- Load balancing during heavy periods
- Keeping primary runner free for urgent builds

✅ **When to use primary runner (default):**
- Regular production builds
- Automated CI/CD builds
- Normal day-to-day operations

---

## 🔧 Troubleshooting

### Runner Not Picking Up Jobs:
1. Ensure runner is started: `cd ~/actions-runners/runner-secondary && ./run.sh`
2. Check you specified `runner_label: "macos-secondary"` in the workflow trigger
3. Verify runner shows as "online" on GitHub

### Remove/Unregister Runner:
```bash
cd ~/actions-runners/runner-secondary
./config.sh remove --token YOUR_NEW_TOKEN
```

### Re-register Runner:
Get a new token from: https://github.com/organizations/LuckyJackpotCasino/settings/actions/runners/new

```bash
cd ~/actions-runners/runner-secondary
./config.sh remove --token OLD_TOKEN
./config.sh \
  --url https://github.com/LuckyJackpotCasino \
  --token NEW_TOKEN \
  --name "MacBook-Pro-Secondary" \
  --labels "self-hosted,macos-secondary" \
  --work _work
```

---

## 📝 Quick Test

Start the runner and test it:

```bash
# Terminal 1: Start the runner
cd ~/actions-runners/runner-secondary
./run.sh

# Terminal 2: Trigger a test build
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="ios" \
  -f runner_label="macos-secondary"
```

Watch Terminal 1 - you should see the build start!

---

**BuildBot 9000** 🤖  
Secondary runner configured and ready for manual builds!

