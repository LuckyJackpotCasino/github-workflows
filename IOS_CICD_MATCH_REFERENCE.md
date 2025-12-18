## iOS CI/CD (Industry Standard): Fastlane Match + Manual Signing on a Self‑Hosted Mac Runner

This is the reference setup we use for Unity iOS builds on GitHub Actions with a **self-hosted Mac runner**.

**Goals**
- Deterministic signing (no surprise changes)
- No interactive prompts (non-interactive CI)
- Scales across many apps (one consistent pattern)
- Shared/persistent workspace is safe even if someone opens Unity locally

---

### What we use

- **Fastlane Match**: Stores iOS signing assets in an encrypted private git repo.
- **Manual signing on CI**: Xcode uses a specific provisioning profile + Distribution certificate.
- **Per-run CI keychain**: Avoids Keychain UI prompts / `errSecInternalComponent`.
- **Unity project can stay Automatic for dev**: CI patches the generated Xcode project to manual signing.

---

## Required GitHub org secrets (names only)

These are Organization-level secrets (granted to all repos that build iOS):

- **`APP_STORE_CONNECT_API_KEY_ID`**
- **`APP_STORE_CONNECT_API_ISSUER_ID`**
- **`APP_STORE_CONNECT_API_KEY_CONTENT`** (base64 of the `.p8`)
- **`MATCH_PASSWORD`** (encryption password for Match repo)

Notes:
- Do **not** store certificates/profiles as GitHub secrets when using Match.
- The Match repo itself stores encrypted artifacts.

---

## Match repo

- Private repo: `LuckyJackpotCasino/ios-certificates`
- Contents (encrypted by `MATCH_PASSWORD`):
  - `certs/distribution/*.p12` and `*.cer`
  - `profiles/appstore/*.mobileprovision`

### Adding a new app to iOS CI/CD

When you add a new iOS bundle id (e.g. a new Unity game), you must create its App Store provisioning profile in Match.

Checklist:
- In Apple Developer → Identifiers, ensure the App ID capabilities are enabled (Game Center, Sign in with Apple, IAP, etc.)
- Run Match in **admin mode** (readonly: false) to create the profile in the Match repo
- CI runs Match **readonly: true**

---

## Self-hosted runner approach

### Shared workspace (fast builds)
The workflow uses a persistent workspace on the Mac runner:
- First run clones the repo
- Later runs `fetch + reset --hard` for speed

### Guardrail: Unity cannot be open during CI
Unity batchmode builds fail if another Unity instance has the project open.
Our workflow includes a guard step:
- kill Unity/Unity Hub processes
- remove `Temp/UnityLockfile` if present

---

## CI signing flow (high level)

1. **Sync signing assets via Match (readonly)**
2. **Create a per-run CI keychain**
3. **Install Match certs into the CI keychain**
4. **Patch Unity-generated Xcode project to Manual signing**
   - set `ProvisioningStyle = Manual`
   - set `CODE_SIGN_STYLE = Manual`
   - set `PROVISIONING_PROFILE(_SPECIFIER)_APP` to Match profile values
   - set Distribution identity for Release archive
5. `xcodebuild archive` (manual signing)
6. `xcodebuild -exportArchive` using ExportOptions.plist
7. Upload via `altool` using App Store Connect API key

---

## Common failures and fixes

### 1) "Multiple Unity instances cannot open the same project"
- Cause: Unity Editor was open locally on the runner.
- Fix: Ensure the workflow kill/lock cleanup step runs before Unity batchmode.

### 2) "requires a provisioning profile with Game Center/IAP/Sign in with Apple"
- Cause: App ID capabilities weren’t enabled when profile was generated.
- Fix:
  - Enable capabilities on Apple Developer App ID
  - Regenerate the Match App Store profile (readonly false + force)

### 3) `errSecInternalComponent` during CodeSign
- Cause: Keychain access / partition list / UI prompt issues.
- Fix: Always use a **fresh per-run CI keychain** and set partition list.

### 4) Pods signing errors
- Cause: Passing CODE_SIGN_* overrides on the `xcodebuild` CLI can accidentally apply to Pods targets.
- Fix: Patch the main Unity Xcode project settings; avoid global CLI overrides that spill into Pods.

---

## Where this is implemented

- Reusable workflow: `LuckyJackpotCasino/github-workflows/.github/workflows/unity-ios-build-auto-signing.yml`
- Game workflows call it like:
  - `uses: LuckyJackpotCasino/github-workflows/.github/workflows/unity-ios-build-auto-signing.yml@main`
  - with inputs: `team_id`, `app_bundle_id`, `unity_version`, `build_method`

---

## Security notes

- Never commit `.p8` keys, `.p12` certificates, or provisioning profiles to app repos.
- Keep Match repo private and encrypted.
- Keep `MATCH_PASSWORD` and App Store Connect API key as GitHub Secrets only.
