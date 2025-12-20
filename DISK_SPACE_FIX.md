# Build Server Disk Space Issue - Fix Guide

## 🚨 Problem

**Error:** `No space left on device`  
**Impact:** Builds fail during "Upload to Google Play" step  
**Cause:** Build runner disk is full

---

## 🔍 Diagnosis Commands

### 1. Check Overall Disk Space
```bash
df -h /
```

### 2. Find Large Directories
```bash
# Check home directory
du -sh ~/* 2>/dev/null | sort -hr | head -20

# Check runner workspace
du -sh ~/actions-runner/_work/* 2>/dev/null | sort -hr

# Check Library folder (caches, logs)
du -sh ~/Library/* 2>/dev/null | sort -hr | head -20
```

### 3. Find Large Unity Files
```bash
# Unity cache
du -sh ~/Library/Unity 2>/dev/null

# Unity logs
du -sh ~/Library/Logs/Unity 2>/dev/null

# Xcode DerivedData
du -sh ~/Library/Developer/Xcode/DerivedData 2>/dev/null
```

---

## 🧹 Clean-Up Commands

### Safe to Delete:

#### 1. **Runner Diagnostic Logs** (Usually the culprit)
```bash
# Check size
du -sh ~/actions-runner/_diag

# Clean old logs (keep last 7 days)
find ~/actions-runner/_diag -name "*.log" -mtime +7 -delete
```

#### 2. **Unity Cache**
```bash
# Unity package cache
rm -rf ~/Library/Unity/cache/packages/*

# Unity asset cache
rm -rf ~/Library/Caches/com.unity3d.UnityEditor5.x
```

#### 3. **Xcode DerivedData**
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

#### 4. **Old Build Artifacts in Runner Workspace**
```bash
# List old builds
ls -lht ~/actions-runner/_work/

# Clean builds older than 30 days
find ~/actions-runner/_work -maxdepth 2 -type d -mtime +30 -exec rm -rf {} +
```

#### 5. **Homebrew Cache**
```bash
brew cleanup
```

#### 6. **System Logs**
```bash
sudo rm -rf /var/log/*.log.*
sudo rm -rf /var/log/*.gz
```

---

## 🚀 Quick Fix Script

Create this script for easy cleanup:

```bash
#!/bin/bash
# ~/cleanup-build-server.sh

echo "🧹 Cleaning build server..."

# Runner logs (older than 7 days)
echo "📋 Cleaning runner logs..."
find ~/actions-runner/_diag -name "*.log" -mtime +7 -delete 2>/dev/null

# Xcode DerivedData
echo "🔨 Cleaning Xcode DerivedData..."
rm -rf ~/Library/Developer/Xcode/DerivedData/* 2>/dev/null

# Unity cache
echo "🎮 Cleaning Unity cache..."
rm -rf ~/Library/Unity/cache/packages/* 2>/dev/null
rm -rf ~/Library/Caches/com.unity3d.UnityEditor5.x 2>/dev/null

# Homebrew cache
echo "🍺 Cleaning Homebrew..."
brew cleanup 2>/dev/null

echo ""
echo "✅ Cleanup complete!"
echo ""
df -h /
```

Make it executable:
```bash
chmod +x ~/cleanup-build-server.sh
```

---

## 🔄 After Cleanup

### 1. Restart the Runner
```bash
cd ~/actions-runner
./svc.sh stop
./svc.sh start
```

### 2. Retry Failed Builds
```bash
# Retry fvg-keno
gh run rerun 20382613488 --repo LuckyJackpotCasino/fvg-keno

# Or trigger new build
gh workflow run fvg-keno-builds.yml \
  --repo LuckyJackpotCasino/fvg-keno \
  -f build_platforms="aab"
```

---

## 📊 Monitoring

### Check Space Regularly
```bash
# Current usage
df -h / | awk 'NR==2 {print "Used: " $5 " (" $3 " / " $2 ")"}'

# Alert if > 80% full
USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
  echo "⚠️  Disk is ${USAGE}% full - cleanup needed!"
fi
```

### Set Up Automatic Cleanup (cron)
```bash
# Add to crontab (cleanup weekly on Sunday at 2 AM)
crontab -e

# Add this line:
0 2 * * 0 ~/cleanup-build-server.sh
```

---

## 🎯 Prevention

### 1. **Runner Log Rotation**
The runner logs in `~/actions-runner/_diag` can grow massive. Clean them regularly.

### 2. **Workspace Cleanup**
Old builds in `~/actions-runner/_work` accumulate. The persistent workspace strategy keeps Library folders but can still grow.

### 3. **Monitor Disk Usage**
Run `df -h /` regularly or set up alerts.

### 4. **Unity Cache Management**
Unity package cache can grow to 10GB+. Clear it monthly.

---

## 📝 Quick Reference

| Issue | Command |
|-------|---------|
| Check disk space | `df -h /` |
| Find large files | `du -sh ~/* \| sort -hr \| head -20` |
| Clean runner logs | `find ~/actions-runner/_diag -name "*.log" -mtime +7 -delete` |
| Clean Xcode | `rm -rf ~/Library/Developer/Xcode/DerivedData/*` |
| Clean Unity | `rm -rf ~/Library/Unity/cache/packages/*` |
| Restart runner | `cd ~/actions-runner && ./svc.sh restart` |

---

## 🚨 Emergency: Completely Full Disk

If disk is 100% full and nothing works:

```bash
# 1. Stop runner immediately
cd ~/actions-runner
./svc.sh stop

# 2. Delete runner logs (frees up space fast)
rm -rf ~/actions-runner/_diag/*.log

# 3. Delete Xcode DerivedData
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# 4. Check if enough space now
df -h /

# 5. Restart runner
./svc.sh start
```

---

**BuildBot 9000** 🤖  
_Fix this when you get to the build server, then retry the failed builds!_

