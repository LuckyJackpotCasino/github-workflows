# Free Vegas Games - Quick Reference Card

## ✅ Setup Complete

### Workflows Created:
- ✅ `fvg-multicardkeno` → workflow with team_id: `7J3C49GFS8`
- ✅ `fvg-keno` → workflow with team_id: `7J3C49GFS8`
- ✅ `fvg-fourcardkeno` → workflow with team_id: `7J3C49GFS8`

### Dashboard:
- ✅ All 3 FVG games added with 🎲 FVG label
- ✅ Running at http://localhost:8765

## 🔑 Team IDs (Public - Not Secrets)

| Studio | Team ID | Location |
|--------|---------|----------|
| Lucky Jackpot Casino | `D3H7LWSJL6` | Hardcoded in each LJC workflow |
| Free Vegas Games | `7J3C49GFS8` | Hardcoded in each FVG workflow |

## 📋 Required Secrets Per FVG Repo

Add to **each** FVG repository: `fvg-multicardkeno`, `fvg-keno`, `fvg-fourcardkeno`

### iOS Secrets (3):
```
APP_STORE_CONNECT_KEY_ID       (Your FVG key ID)
APP_STORE_CONNECT_ISSUER_ID    (Your FVG issuer ID)
APP_STORE_CONNECT_KEY_P8       (Your FVG .p8 file contents)
```

### Android Secrets (5) - Already set ✅:
```
GOOGLE_SERVICE_ACCOUNT_JSON
ANDROID_KEYSTORE_BASE64
ANDROID_KEYSTORE_PASSWORD
ANDROID_KEY_ALIAS
ANDROID_KEY_PASSWORD
```

## 🚀 Quick Commands

### Add iOS secrets to all 3 FVG repos:
\`\`\`bash
for repo in fvg-multicardkeno fvg-keno fvg-fourcardkeno; do
  gh secret set APP_STORE_CONNECT_KEY_ID -b "YOUR_KEY_ID" --repo LuckyJackpotCasino/$repo
  gh secret set APP_STORE_CONNECT_ISSUER_ID -b "YOUR_ISSUER_ID" --repo LuckyJackpotCasino/$repo
  gh secret set APP_STORE_CONNECT_KEY_P8 < your-fvg-key.p8 --repo LuckyJackpotCasino/$repo
done
\`\`\`

### Test builds:
\`\`\`bash
# Android (should work now)
gh workflow run fvg-multicardkeno-builds.yml --repo LuckyJackpotCasino/fvg-multicardkeno -f build_platforms="aab"

# iOS (after adding secrets)
gh workflow run fvg-multicardkeno-builds.yml --repo LuckyJackpotCasino/fvg-multicardkeno -f build_platforms="ios"
\`\`\`

## 📊 What Works Now

| Platform | Status | Notes |
|----------|--------|-------|
| Android AAB | ✅ Ready | Android keys already set |
| Amazon APK | ✅ Ready | Android keys already set |
| iOS | ⚙️ Pending | Add 3 secrets per repo |

---

**BuildBot 9000** 🤖
