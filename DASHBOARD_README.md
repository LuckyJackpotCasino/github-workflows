# 🎰 Build Dashboard

Live web dashboard for monitoring and triggering GitHub Actions builds across all Lucky Jackpot Casino apps.

## 🚀 Quick Start

### Prerequisites
- **Python 3** (pre-installed on macOS)
- **GitHub CLI (`gh`)** - [Install here](https://cli.github.com/)
- **Authenticated with GitHub** - Run `gh auth login` if needed

### Running the Dashboard

**Option 1: Using the start script**
```bash
cd github-workflows
./start-dashboard.sh
```

**Option 2: Manual start**
```bash
cd github-workflows
python3 server.py
```

Then open in your browser:
```
http://localhost:3000
```

## ✨ Features

### Real-time Status Monitoring
- Live status for all 9 casino apps
- Separate columns for iOS, AAB (Google Play), and Amazon builds
- Auto-refreshes every 30 seconds
- Color-coded status badges:
  - ✅ **Success** - Build completed successfully
  - 🚧 **Building** - Currently running
  - ⏳ **Queued** - Waiting to start
  - ⏭️ **Skipped** - Not run (other platform selected)
  - ❌ **Failed** - Build failed
  - ⊘ **Cancelled** - Manually cancelled
  - – **Not Run** - Not started yet

### Build Triggers

**Bulk Actions** (top of dashboard):
- 🎮 **All Apps - All Platforms** - Trigger all 9 apps for all 3 platforms (27 builds!)
- 🍎 **All Apps - iOS Only** - Trigger iOS builds for all apps
- 🤖 **All Apps - Google Play** - Trigger AAB builds for all apps
- 📦 **All Apps - Amazon** - Trigger Amazon builds for all apps

**Per-App Actions** (in each row):
- 🚀 **All** - Build all 3 platforms for this app
- 🍎 **iOS** - Build iOS only
- 🤖 **AAB** - Build Google Play only
- 📦 **Amazon** - Build Amazon only

## 📁 Files

```
github-workflows/
├── dashboard.html       # Frontend UI
├── server.py           # Backend API server
├── start-dashboard.sh  # Quick start script
└── DASHBOARD_README.md # This file
```

## 🔧 How It Works

1. **Backend (`server.py`)**:
   - Runs a local HTTP server on port 3000
   - Uses `gh` CLI to fetch build status from GitHub Actions
   - Provides REST API endpoints for status and triggers
   - Caches results for 30 seconds to reduce API calls

2. **Frontend (`dashboard.html`)**:
   - Single-page web app
   - Fetches data from local API
   - Updates status cells in-place (no flickering)
   - Sends trigger requests via POST

## 🌐 Using on Different Computers

The dashboard works on **any Mac or Linux machine** with:
1. Python 3 installed
2. GitHub CLI installed and authenticated
3. Access to the LuckyJackpotCasino GitHub organization

**To use on your MacBook:**
```bash
# 1. Clone/pull the repo
cd ~/path/to/github-workflows
git pull

# 2. Make sure gh is authenticated
gh auth status

# 3. Start the dashboard
./start-dashboard.sh

# 4. Open browser to http://localhost:3000
```

## 🛑 Stopping the Dashboard

Press `Ctrl+C` in the terminal where the server is running, or:

```bash
# Find and kill the server process
pkill -f "python3 server.py"
```

## 🐛 Troubleshooting

### Port 3000 already in use
```bash
# Kill existing server
lsof -ti :3000 | xargs kill -9

# Start again
./start-dashboard.sh
```

### gh CLI certificate errors
This is a known issue with some network configurations. The dashboard will still work, but command-line triggers might fail. Use the dashboard's web UI buttons instead.

### Dashboard shows all "pending"
- Check that `gh` CLI is authenticated: `gh auth status`
- Check GitHub Actions are accessible: `gh run list --repo LuckyJackpotCasino/kenocasino`
- Wait 30 seconds for cache to clear and data to refresh

## 📊 API Endpoints

The server provides these endpoints:

- `GET /` - Dashboard HTML
- `GET /status/<app>` - Get status for specific app
- `GET /status` - Get status for all apps
- `POST /trigger/<app>/<platform>` - Trigger single app build
- `POST /trigger-bulk/<platform>` - Trigger all apps for platform

## 🎯 Use Cases

### SDK Testing Workflow
When BoostOps releases a new SDK:
1. Open dashboard
2. Click "🍎 All Apps - iOS Only"
3. Monitor builds in real-time
4. After all iOS succeed, click "🤖 All Apps - Google Play"
5. Then "📦 All Apps - Amazon"

### Individual App Testing
1. Make changes to an app repo
2. Open dashboard
3. Click the specific platform button for that app
4. Watch build progress live

### Build Status at a Glance
- Open dashboard in browser
- Leave it open and check throughout the day
- Auto-refreshes every 30 seconds

## 📝 Notes

- **Cache Duration**: Status is cached for 30 seconds to reduce GitHub API calls
- **Build Number Offsets**: Each app has different offsets (shown in Offsets column)
- **Self-hosted Runner**: All builds run on a single self-hosted runner (sequential)
- **Concurrent Limits**: Be mindful of triggering too many builds at once

---

**Last Updated**: December 14, 2024
**Version**: 1.0
