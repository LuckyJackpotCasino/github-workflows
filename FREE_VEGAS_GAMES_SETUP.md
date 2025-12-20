# Free Vegas Games - CI/CD Setup Instructions

## 🎲 Overview

The Free Vegas Games studio uses **repository-level secrets** to override the Lucky Jackpot Casino org-level secrets. This allows both studios to use identical workflows while maintaining separate credentials.

## 📋 Required Secrets for Each FVG Repository

You need to add these secrets to **each FVG repository** (fvg-multicardkeno, fvg-keno, fvg-fourcardkeno):

**Note:** The Apple Team ID (`7J3C49GFS8`) is **hardcoded in the workflow** - it's not a secret, just a public identifier.

### Apple / iOS Secrets

```
APP_STORE_CONNECT_KEY_ID
  - App Store Connect API Key ID
  - Example: "YYYYYYYY" (8 characters)

APP_STORE_CONNECT_ISSUER_ID
  - App Store Connect API Issuer ID
  - Example: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" (UUID format)

APP_STORE_CONNECT_KEY_P8
  - Full contents of your .p8 private key file
  - Include the BEGIN/END lines:
    -----BEGIN PRIVATE KEY-----
    (key contents)
    -----END PRIVATE KEY-----
```

### Google Play / Android Secrets

```
GOOGLE_SERVICE_ACCOUNT_JSON
  - Full JSON contents of your Google Play service account
  - This is the JSON file downloaded from Google Cloud Console
  - Must have permissions to upload AABs to Google Play

ANDROID_KEYSTORE_BASE64
  - Base64-encoded Android keystore file
  - Generate with: base64 -i your-keystore.jks | tr -d '\n'

ANDROID_KEYSTORE_PASSWORD
  - Password for the keystore file

ANDROID_KEY_ALIAS
  - Alias name for the signing key in the keystore

ANDROID_KEY_PASSWORD
  - Password for the specific key alias
```

### Amazon Appstore Secrets (Optional)

```
AMAZON_CLIENT_ID
  - Amazon Appstore client ID (if different from org)

AMAZON_CLIENT_SECRET
  - Amazon Appstore client secret (if different from org)
```

## 🔧 How to Add Repository Secrets

### Via GitHub Web UI:

1. Go to the repository: `https://github.com/LuckyJackpotCasino/fvg-multicardkeno`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret name and value (3 iOS secrets + 5 Android secrets)
5. Repeat for all 3 FVG repositories

### Via GitHub CLI (Faster):

```bash
# Set Free Vegas Games Apple credentials for all 3 repos
for repo in fvg-multicardkeno fvg-keno fvg-fourcardkeno; do
  gh secret set APP_STORE_CONNECT_KEY_ID -b "YOUR_KEY_ID" --repo LuckyJackpotCasino/$repo
  gh secret set APP_STORE_CONNECT_ISSUER_ID -b "YOUR_ISSUER_ID" --repo LuckyJackpotCasino/$repo
  gh secret set APP_STORE_CONNECT_KEY_P8 < your-key.p8 --repo LuckyJackpotCasino/$repo
done

# Set Google Play credentials (if Android keys are ready)
for repo in fvg-multicardkeno fvg-keno fvg-fourcardkeno; do
  gh secret set GOOGLE_SERVICE_ACCOUNT_JSON < fvg-service-account.json --repo LuckyJackpotCasino/$repo
  gh secret set ANDROID_KEYSTORE_BASE64 -b "$(base64 -i fvg-keystore.jks | tr -d '\n')" --repo LuckyJackpotCasino/$repo
  gh secret set ANDROID_KEYSTORE_PASSWORD -b "YOUR_KEYSTORE_PASSWORD" --repo LuckyJackpotCasino/$repo
  gh secret set ANDROID_KEY_ALIAS -b "YOUR_KEY_ALIAS" --repo LuckyJackpotCasino/$repo
  gh secret set ANDROID_KEY_PASSWORD -b "YOUR_KEY_PASSWORD" --repo LuckyJackpotCasino/$repo
done
```

## ⚠️ Current Status

### ✅ Completed:
- Workflows created for all 3 FVG games
- Dashboard updated to show FVG games
- Android/AAB secrets configured ✅

### ⚙️ Pending:
- iOS secrets need to be added to each FVG repo
- Once iOS secrets are added, iOS builds will work automatically

## 🚀 Testing the Setup

### Test Android Builds (Should work now):
```bash
# Trigger from dashboard or via CLI:
gh workflow run fvg-multicardkeno-builds.yml --repo LuckyJackpotCasino/fvg-multicardkeno -f build_platforms="aab"
```

### Test iOS Builds (After adding iOS secrets):
```bash
gh workflow run fvg-multicardkeno-builds.yml --repo LuckyJackpotCasino/fvg-multicardkeno -f build_platforms="ios"
```

## 📊 Dashboard

View all builds at: **http://localhost:8765**

The dashboard now shows:
- 🎰 Lucky Jackpot Casino games (9 apps)
- 🎲 Free Vegas Games (3 apps)
- Separate studio labels for easy identification

## 🔍 How Repository Override Works

```
GitHub Organization: LuckyJackpotCasino
├── Org-Level Secrets (Lucky Jackpot Casino credentials)
│   ├── APPLE_TEAM_ID=D3H7LWSJL6
│   ├── APP_STORE_CONNECT_KEY_ID=...
│   └── ...
│
├── Repo: blackjack21 ✅ Uses org secrets
├── Repo: vintageslots ✅ Uses org secrets
│
└── Repo: fvg-multicardkeno
    ├── APPLE_TEAM_ID=XXXXXXXXXX  ⚡ Overrides org secret
    ├── APP_STORE_CONNECT_KEY_ID=... ⚡ Overrides org secret
    └── ... (all FVG secrets override org secrets)
```

**Result:** Same workflow, different credentials automatically based on repository! 🎉

## 📝 Workflow Details

Each FVG game has a workflow that:
- Uses the shared reusable workflows (`unity-android-build.yml`, `unity-ios-build-auto-signing.yml`)
- Automatically picks up FVG repo secrets (when iOS build fails, it means iOS secrets aren't set yet)
- Inherits all Lucky Jackpot workflow features (build matrix, artifact handling, etc.)

## 🆘 Troubleshooting

### iOS Build Fails:
- **Cause:** iOS secrets not set for the FVG repo
- **Fix:** Add the Apple/iOS secrets to the repository (see above)

### Android Build Fails:
- **Cause:** Keystore or Google Play secrets missing/incorrect
- **Fix:** Verify `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEY_ALIAS`, etc. are correct

### Wrong Credentials Used:
- **Cause:** Repository secret not set, falling back to org secret
- **Fix:** Ensure secret name matches exactly (case-sensitive)

---

**BuildBot 9000** 🤖 - Autonomous CI/CD Engineer

