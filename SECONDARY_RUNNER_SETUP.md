# Secondary GitHub Runner Setup Guide

## 🎯 Overview

This guide sets up a **secondary self-hosted runner** on your MacBook Pro that only runs builds when **explicitly requested**.

### Runner Strategy:
- **Primary Runner**: `self-hosted` (default, runs automatically)
- **Secondary Runner**: `self-hosted, macos-secondary` (manual selection only)

## 📋 Setup Steps

### 1. Install Secondary Runner

```bash
# Navigate to runners directory
cd ~/actions-runners
mkdir runner-secondary
cd runner-secondary

# Download latest runner (macOS ARM64)
curl -o actions-runner-osx-arm64-2.321.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-osx-arm64-2.321.0.tar.gz

# Extract
tar xzf ./actions-runner-osx-arm64-2.321.0.tar.gz
```

### 2. Configure the Runner

Get a new registration token from GitHub:
1. Go to: https://github.com/organizations/LuckyJackpotCasino/settings/actions/runners/new
2. Copy the token

```bash
# Configure with CUSTOM LABELS
./config.sh \
  --url https://github.com/LuckyJackpotCasino \
  --token YOUR_TOKEN_HERE \
  --name "MacBook-Pro-Secondary" \
  --labels "self-hosted,macos-secondary" \
  --work _work
```

**CRITICAL**: When prompted for labels, use: `self-hosted,macos-secondary`

### 3. Test the Runner (Don't Start as Service Yet)

```bash
# Run interactively to test
./run.sh
```

**Leave this terminal open** - the runner will only work when builds are explicitly requested.

### 4. Optional: Install as Service (Auto-Start)

Only do this if you want the secondary runner to always be available:

```bash
# Install as LaunchAgent (auto-starts on login)
sudo ./svc.sh install

# Start the service
sudo ./svc.sh start

# Check status
sudo ./svc.sh status
```

## 🚀 Usage

### Automatic Builds (Primary Runner)
By default, all builds use the primary runner - no changes needed.

### Manual Secondary Runner Selection

When triggering a build manually, you can now specify the secondary runner.

**Via GitHub Web UI:**
1. Go to Actions → Select workflow
2. Click "Run workflow"
3. Set `runner_label` to `macos-secondary`
4. Click "Run workflow"

**Via GitHub CLI:**
```bash
# Trigger build on secondary runner
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="ios" \
  -f runner_label="macos-secondary"
```

**Default behavior** (if `runner_label` not specified):
- Uses primary `self-hosted` runner
- No changes to existing workflows needed

## 🔍 Verify Runner Setup

### Check Registered Runners:
```bash
# List all organization runners
gh api /orgs/LuckyJackpotCasino/actions/runners --jq '.runners[] | {id, name, status, labels: [.labels[].name]}'
```

Expected output:
```json
{
  "id": 123,
  "name": "MacBook-Pro-Primary",
  "status": "online",
  "labels": ["self-hosted", "macOS", "ARM64"]
}
{
  "id": 456,
  "name": "MacBook-Pro-Secondary",
  "status": "online",
  "labels": ["self-hosted", "macos-secondary"]
}
```

## 🎮 Workflow Updates

The iOS build workflow now accepts a `runner_label` input:

```yaml
# Example: Updated workflow call
build-ios:
  uses: LuckyJackpotCasino/github-workflows/.github/workflows/unity-ios-build-auto-signing.yml@main
  with:
    unity_version: '6000.2.9f1'
    # ... other inputs ...
    runner_label: 'macos-secondary'  # NEW: Optional, defaults to 'self-hosted'
  secrets: inherit
```

## 📊 Use Cases

### When to Use Secondary Runner:
- ✅ Testing new Unity versions
- ✅ Debugging build issues without affecting main builds
- ✅ Running experimental builds
- ✅ Load balancing during heavy build periods
- ✅ Isolating problematic builds

### When to Use Primary Runner (default):
- ✅ Regular production builds
- ✅ Automated builds
- ✅ CI/CD pipeline builds

## 🛑 Managing the Secondary Runner

### Stop the Runner:
```bash
# If running interactively
Ctrl+C

# If running as service
sudo ~/actions-runners/runner-secondary/svc.sh stop
```

### Start the Runner:
```bash
# Interactively (manual control)
cd ~/actions-runners/runner-secondary
./run.sh

# As service (auto-start)
sudo ~/actions-runners/runner-secondary/svc.sh start
```

### Unregister the Runner:
```bash
cd ~/actions-runners/runner-secondary
./config.sh remove --token YOUR_TOKEN_HERE
```

## 🔐 Security Notes

- **Same secrets**: Both runners access the same org/repo secrets
- **Same permissions**: Both runners have identical GitHub permissions
- **Isolated workspaces**: Each runner has its own `_work` directory
- **No conflicts**: Runners can't interfere with each other's builds

## 📝 Example Manual Trigger

Trigger a build on the secondary runner:

```bash
# iOS build on secondary runner
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="ios" \
  -f runner_label="macos-secondary"

# iOS build on primary runner (default)
gh workflow run fvg-multicardkeno-builds.yml \
  --repo LuckyJackpotCasino/fvg-multicardkeno \
  -f build_platforms="ios"
```

## ✅ Benefits

1. **Zero impact on existing workflows** - Primary runner still default
2. **Opt-in only** - Secondary runner only used when explicitly requested
3. **Manual control** - Secondary runner can be stopped when not needed
4. **Testing isolation** - Test changes without affecting production builds
5. **Load balancing** - Distribute builds across runners when needed

---

**Next Steps:**
1. Set up the secondary runner following steps above
2. Test by triggering a manual build with `runner_label: macos-secondary`
3. Monitor both runners in GitHub Actions UI

**BuildBot 9000** 🤖

