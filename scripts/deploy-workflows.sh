#!/bin/bash
#
# BuildBot 9000 - Deploy Caller Workflows to All App Repos
#
# Creates the GitHub Actions caller workflow in each app repo via the API.
# Uses the kenocasino workflow as a template, customized per app.
#
# Usage:
#   ./deploy-workflows.sh              # Deploy to all apps missing workflows
#   ./deploy-workflows.sh --force      # Overwrite existing workflows
#   ./deploy-workflows.sh blackjack21  # Deploy to specific app only
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ORG="LuckyJackpotCasino"
TEAM_ID="D3H7LWSJL6"
UNITY_VERSION="6000.2.9f1"

FORCE=false
TARGET_APP=""
for arg in "$@"; do
  case $arg in
    --force) FORCE=true ;;
    *) TARGET_APP="$arg" ;;
  esac
done

generate_workflow() {
  local APP=$1
  local DISPLAY_NAME=$2
  local AAB_OFFSET=$3
  local AMAZON_OFFSET=$4
  local PACKAGE=$5
  local ARTIFACT_PREFIX=$6

  cat <<WORKFLOW_EOF
name: ${DISPLAY_NAME} - All Platforms

on:
  workflow_dispatch:
    inputs:
      build_platforms:
        description: 'Platforms to build (comma-separated: aab,amazon,ios)'
        required: true
        default: 'aab,amazon,ios'

jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      build_aab: \${{ steps.set-matrix.outputs.build_aab }}
      build_amazon: \${{ steps.set-matrix.outputs.build_amazon }}
      build_ios: \${{ steps.set-matrix.outputs.build_ios }}
    steps:
      - name: Determine Build Matrix
        id: set-matrix
        run: |
          if [ "\${{ github.event_name }}" == "workflow_dispatch" ]; then
            PLATFORMS="\${{ github.event.inputs.build_platforms }}"
          else
            PLATFORMS="aab,amazon,ios"
          fi

          [[ "\$PLATFORMS" == *"aab"* ]] && echo "build_aab=true" >> \$GITHUB_OUTPUT || echo "build_aab=false" >> \$GITHUB_OUTPUT
          [[ "\$PLATFORMS" == *"amazon"* ]] && echo "build_amazon=true" >> \$GITHUB_OUTPUT || echo "build_amazon=false" >> \$GITHUB_OUTPUT
          [[ "\$PLATFORMS" == *"ios"* ]] && echo "build_ios=true" >> \$GITHUB_OUTPUT || echo "build_ios=false" >> \$GITHUB_OUTPUT

  build-aab:
    needs: setup
    if: needs.setup.outputs.build_aab == 'true'
    uses: ${ORG}/github-workflows/.github/workflows/unity-android-build.yml@main
    with:
      unity_version: '${UNITY_VERSION}'
      build_method: 'RemoteBuilder.BuildGooglePlay'
      build_type: 'aab'
      build_number_offset: '${AAB_OFFSET}'
      repository: '${ORG}/${APP}'
      artifact_name: '${ARTIFACT_PREFIX}-AAB'
      package_name: '${PACKAGE}'
      upload_artifact: false
    secrets: inherit

  build-ios:
    needs: setup
    if: needs.setup.outputs.build_ios == 'true'
    uses: ${ORG}/github-workflows/.github/workflows/unity-ios-build-auto-signing.yml@main
    with:
      unity_version: '${UNITY_VERSION}'
      build_method: 'RemoteBuilder.BuildiOS'
      repository: '${ORG}/${APP}'
      artifact_name: '${ARTIFACT_PREFIX}-iOS'
      team_id: '${TEAM_ID}'
      app_bundle_id: '${PACKAGE}'
    secrets: inherit

  build-amazon:
    needs: setup
    if: needs.setup.outputs.build_amazon == 'true'
    uses: ${ORG}/github-workflows/.github/workflows/unity-android-build.yml@main
    with:
      unity_version: '${UNITY_VERSION}'
      build_method: 'RemoteBuilder.BuildAmazon'
      build_type: 'apk'
      build_number_offset: '${AMAZON_OFFSET}'
      repository: '${ORG}/${APP}'
      artifact_name: '${ARTIFACT_PREFIX}-AMAZON'
      upload_artifact: true
    secrets: inherit
WORKFLOW_EOF
}

# App configs: app_name|display_name|aab_offset|amazon_offset|package_name|artifact_prefix|workflow_filename
CONFIGS=(
  "blackjack21|Blackjack 21|200|100|com.luckyjackpotcasino.blackjack21|Blackjack21|blackjack-builds.yml"
  "videopokercasino|Video Poker Casino|700|600|com.luckyjackpotcasino.videopokercasino|VideoPokerCasino|videopokercasino-builds.yml"
  "multihandpoker|Multi Hand Poker|700|600|com.luckyjackpotcasino.multihandpoker|MultiHandPoker|multihandpoker-builds.yml"
  "keno4card|Keno 4 Card|300|200|com.luckyjackpotcasino.keno4card|Keno4Card|keno4card-builds.yml"
  "keno20card|Keno 20 Card|400|300|com.luckyjackpotcasino.keno20card|Keno20Card|keno20card-builds.yml"
  "kenosuper4x|Keno Super 4X|600|500|com.luckyjackpotcasino.kenosuper4x|KenoSuper4X|kenosuper4x-builds.yml"
  "roulette|Roulette|600|500|com.luckyjackpotcasino.roulette|Roulette|roulette-builds.yml"
  "vintageslots|Vintage Slots|600|500|com.luckyjackpotcasino.vintageslots|VintageSlots|vintageslots-builds.yml"
)

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  BuildBot 9000 - Deploy Caller Workflows${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

DEPLOYED=0
SKIPPED=0
FAILED=0

for CONFIG in "${CONFIGS[@]}"; do
  IFS='|' read -r APP DISPLAY_NAME AAB_OFFSET AMAZON_OFFSET PACKAGE ARTIFACT_PREFIX WORKFLOW_FILE <<< "$CONFIG"

  if [ -n "$TARGET_APP" ] && [ "$APP" != "$TARGET_APP" ]; then
    continue
  fi

  echo -ne "${BLUE}$APP${NC} ($WORKFLOW_FILE): "

  EXISTING=$(gh api "repos/$ORG/$APP/contents/.github/workflows/$WORKFLOW_FILE" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sha',''))" 2>/dev/null || echo "")
  if [ -n "$EXISTING" ] && ! $FORCE; then
    echo -e "${YELLOW}already exists (use --force to overwrite)${NC}"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  CONTENT=$(generate_workflow "$APP" "$DISPLAY_NAME" "$AAB_OFFSET" "$AMAZON_OFFSET" "$PACKAGE" "$ARTIFACT_PREFIX")
  ENCODED=$(echo "$CONTENT" | base64)

  if [ -n "$EXISTING" ]; then
    RESULT=$(gh api "repos/$ORG/$APP/contents/.github/workflows/$WORKFLOW_FILE" \
      --method PUT \
      --field "message=Add GitHub Actions build workflow" \
      --field "content=$ENCODED" \
      --field "sha=$EXISTING" \
      --jq '.commit.sha' 2>&1)
  else
    RESULT=$(gh api "repos/$ORG/$APP/contents/.github/workflows/$WORKFLOW_FILE" \
      --method PUT \
      --field "message=Add GitHub Actions build workflow" \
      --field "content=$ENCODED" \
      --jq '.commit.sha' 2>&1)
  fi

  if [ $? -eq 0 ] && [ -n "$RESULT" ]; then
    echo -e "${GREEN}deployed${NC} (${RESULT:0:8})"
    DEPLOYED=$((DEPLOYED + 1))
  else
    echo -e "${RED}failed - $RESULT${NC}"
    FAILED=$((FAILED + 1))
  fi

  sleep 0.5
done

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}DEPLOY SUMMARY:${NC}"
echo -e "  Deployed: $DEPLOYED  |  Skipped: $SKIPPED  |  Failed: $FAILED"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
