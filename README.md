# GitHub Workflows - Lucky Jackpot Casino

Reusable GitHub Actions workflows for Unity game builds across all 12 casino apps.

## 🎯 Purpose

Centralized workflows that can be called from any app repository. This allows:
- **One place to fix bugs** - update here, all apps get it
- **Consistent builds** - all apps use the same proven workflow
- **Easy feature rollouts** - add new features once, deploy everywhere

## 📁 Repository Structure

```
github-workflows/
├── .github/workflows/
│   ├── unity-android-build.yml          # Reusable Android workflow
│   └── unity-ios-build-auto-signing.yml # Reusable iOS workflow
├── scripts/
│   ├── build-all-apps.sh                # Batch build all 12 apps
│   └── build-single-app.sh              # Build specific app
└── README.md
```

## 📁 Workflows

### `unity-android-build.yml`
Builds Android APKs and AABs for Google Play and Amazon.

**Features:**
- Self-hosted runner optimized (persistent workspace for speed)
- Automatic version code management with offsets
- Direct Google Play upload for AAB builds
- GitHub Artifacts for APK builds
- Shallow git clones for speed
- Unity Library folder caching

**Usage:**
```yaml
jobs:
  build-aab:
    uses: LuckyJackpotCasino/github-workflows/.github/workflows/unity-android-build.yml@main
    with:
      unity_version: '6000.2.9f1'
      build_method: 'RemoteBuilder.BuildGooglePlay'
      build_type: 'aab'
      build_number_offset: '500'
      repository: 'LuckyJackpotCasino/yourapp'
      artifact_name: 'YourApp-AAB'
      package_name: 'com.luckyjackpotcasino.yourapp'
      upload_artifact: false
    secrets: inherit
```

### `unity-ios-build-auto-signing.yml`
Builds iOS apps with automatic signing and TestFlight upload.

**Features:**
- Xcode automatic signing via Fastlane
- Certificate and provisioning profile management
- Export compliance auto-configuration
- Direct TestFlight upload
- CocoaPods integration
- iOS 13.0+ deployment target

**Usage:**
```yaml
jobs:
  build-ios:
    uses: LuckyJackpotCasino/github-workflows/.github/workflows/unity-ios-build-auto-signing.yml@main
    with:
      unity_version: '6000.2.9f1'
      build_method: 'RemoteBuilder.BuildiOS'
      repository: 'LuckyJackpotCasino/yourapp'
      artifact_name: 'YourApp-iOS'
      team_id: 'D3H7LWSJL6'
      app_bundle_id: 'com.luckyjackpotcasino.yourapp'
    secrets: inherit
```

## 🛠️ Build Scripts

### `build-all-apps.sh`

Triggers builds for all 12 apps at once. Perfect for testing BoostOps SDK updates across the entire portfolio.

**Usage:**
```bash
# Clone this repo
git clone https://github.com/LuckyJackpotCasino/github-workflows.git
cd github-workflows/scripts

# Build all apps (AAB only - fast SDK testing)
./build-all-apps.sh aab

# Build all apps with multiple platforms
./build-all-apps.sh aab,amazon
./build-all-apps.sh aab,amazon,ios
```

**When to use:**
- ✅ After updating BoostOps SDK submodule
- ✅ Testing SDK changes across all apps
- ✅ Verifying a central workflow change
- ✅ Weekly regression testing

### `build-single-app.sh`

Triggers a build for one specific app.

**Usage:**
```bash
# Build specific app
./build-single-app.sh kenocasino aab
./build-single-app.sh blackjack21 aab,amazon,ios

# Default is all platforms if not specified
./build-single-app.sh videopokercasino
```

**When to use:**
- ✅ Testing a specific app
- ✅ Quick validation of one app
- ✅ App-specific release builds

## 🔐 Required Secrets (Organization Level)

These are set once at the organization level and inherited by all apps:

### Android
- `ANDROID_KEYSTORE_PASSWORD` - Android keystore password
- `GH_SSH_KEY` - SSH key for private submodule access

### iOS
- `APP_STORE_CONNECT_API_KEY_ID` - App Store Connect API Key ID
- `APP_STORE_CONNECT_API_ISSUER_ID` - App Store Connect Issuer ID
- `APP_STORE_CONNECT_API_KEY_CONTENT` - App Store Connect API Key (base64)

### Google Play (Optional, per-app if needed)
- `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` - Service account for Play Store upload

## 📊 Build Integration Status

**Last Updated:** December 14, 2025

| # | App | AAB Offset | Amazon Offset | Workflow | Build Health | Actions |
|---|-----|-----------|---------------|----------|--------------|---------|
| 1 | [blackjack21](https://github.com/LuckyJackpotCasino/blackjack21) | 200 | 100 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/blackjack21/actions) |
| 2 | [keno4card](https://github.com/LuckyJackpotCasino/keno4card) | 300 | 200 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/keno4card/actions) |
| 3 | [keno20card](https://github.com/LuckyJackpotCasino/keno20card) | 400 | 300 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/keno20card/actions) |
| 4 | [kenocasino](https://github.com/LuckyJackpotCasino/kenocasino) | 500 | 400 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/kenocasino/actions) |
| 5 | [kenosuper4x](https://github.com/LuckyJackpotCasino/kenosuper4x) | 600 | 500 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/kenosuper4x/actions) |
| 6 | [roulette](https://github.com/LuckyJackpotCasino/roulette) | 600 | 500 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/roulette/actions) |
| 7 | [vintageslots](https://github.com/LuckyJackpotCasino/vintageslots) | 600 | 500 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/vintageslots/actions) |
| 8 | [videopokercasino](https://github.com/LuckyJackpotCasino/videopokercasino) | 700 | 600 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/videopokercasino/actions) |
| 9 | [multihandpoker](https://github.com/LuckyJackpotCasino/multihandpoker) | 700 | 600 | ✅ Deployed | 📦 Ready | [View](https://github.com/LuckyJackpotCasino/multihandpoker/actions) |

### Build Health Legend
- ✅ **Passing** - All platforms building successfully
- ⚠️ **Warning** - Some builds failing or need attention
- ❌ **Failing** - Critical build failures
- 📦 **Ready** - Workflow deployed, awaiting first build
- 🚧 **Building** - Currently building

### Verifying Build Health

To check build status for all apps:
```bash
# Quick check
for app in blackjack21 keno4card keno20card kenocasino kenosuper4x roulette vintageslots videopokercasino multihandpoker; do
  echo "🔍 $app"
  gh run list --repo LuckyJackpotCasino/$app --limit 1
done

# Or trigger test builds for all apps (AAB only)
cd scripts
./build-all-apps.sh aab
```

### Integration Notes
- ✅ All 9 apps have workflows deployed
- ✅ All workflows use Unity 6000.2.9f1
- ✅ All workflows reference this central repo (`@main`)
- ✅ AAB builds upload directly to Google Play Internal Testing
- ✅ iOS builds upload directly to TestFlight
- ✅ Amazon APKs saved as GitHub Artifacts
- 📊 Build offsets assigned to prevent version conflicts

## 🎮 BoostOps SDK Testing Workflow

Since we're actively developing BoostOps, here's the recommended workflow for testing SDK updates:

### Quick SDK Test (AAB Only - 30-40 minutes total)
```bash
# 1. Update BoostOps in your apps (done separately per app)
# 2. Test across all 12 apps
cd github-workflows/scripts
./build-all-apps.sh aab

# All apps build in parallel → AAB uploaded to Google Play Internal Testing
```

### Full SDK Test (All Platforms - 60-90 minutes total)
```bash
# Test AAB + Amazon + iOS
./build-all-apps.sh aab,amazon,ios
```

### Testing Individual App First
```bash
# Test in one app before rolling out
./build-single-app.sh kenocasino aab

# Once verified, trigger all apps
./build-all-apps.sh aab
```

### Recommended Cadence
- **After SDK updates**: Quick test (AAB only)
- **Weekly**: Full test (all platforms)
- **Before releases**: Full test + manual QA

## 🚀 Migration from Jenkins

These workflows replace the previous Jenkins CI/CD setup with:
- **90% faster builds** (persistent workspace on self-hosted runner)
- **Zero infrastructure costs** (self-hosted runner on existing Mac)
- **Automatic uploads** (Google Play, TestFlight)
- **Modern CI/CD** (GitHub Actions native)

### Build Speed Comparison
- Jenkins: ~20 minutes per build
- GitHub Actions: ~2 minutes per build

### Key Optimizations
- Persistent workspace (no re-cloning)
- Unity Library folder reuse
- Shallow git clones
- Parallel builds (AAB + Amazon + iOS)

## 📖 Documentation

See [BuildBot1000](https://github.com/LuckyJackpotCasino/buildbot1000) for full migration documentation.

## 🛠️ Updating Workflows

To update these workflows for all apps:

1. Make changes to this repository
2. Commit and push to `main` branch
3. All apps using `@main` will automatically use the new version

**Note:** Apps can pin to specific versions using tags if needed:
```yaml
uses: LuckyJackpotCasino/github-workflows/.github/workflows/unity-android-build.yml@v1.0.0
```

## 📊 Version History

- **v1.0.0** (Dec 2025) - Initial migration from Jenkins
  - Android APK/AAB builds
  - iOS automatic signing
  - Google Play auto-upload
  - TestFlight auto-upload
  - Export compliance configuration

---

**BuildBot 9000** 🤖 - Your friendly CI/CD migration assistant

