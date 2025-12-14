# GitHub Workflows - Lucky Jackpot Casino

Reusable GitHub Actions workflows for Unity game builds across all 12 casino apps.

## 🎯 Purpose

Centralized workflows that can be called from any app repository. This allows:
- **One place to fix bugs** - update here, all apps get it
- **Consistent builds** - all apps use the same proven workflow
- **Easy feature rollouts** - add new features once, deploy everywhere

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

## 📱 App Repositories Using These Workflows

1. [kenocasino](https://github.com/LuckyJackpotCasino/kenocasino) ✅
2. [blackjack21](https://github.com/LuckyJackpotCasino/blackjack21) ✅
3. videopoker
4. luckyslots
5. mahjong
6. videopokerclassic
7. videopokerdeluxe
8. videopokersuper
9. wheeloffortune
10. bingo
11. scratchcards
12. doubleucraps

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

