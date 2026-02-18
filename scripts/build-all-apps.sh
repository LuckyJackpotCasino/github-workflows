#!/bin/bash
#
# BuildBot 9000 - Batch Build All Apps
#
# Triggers builds for all 12 casino apps to test BoostOps SDK updates
# Usage:
#   ./build-all-apps.sh [platforms]
#
# Examples:
#   ./build-all-apps.sh aab                    # AAB only (fast, for SDK testing)
#   ./build-all-apps.sh aab,amazon             # AAB + Amazon
#   ./build-all-apps.sh aab,amazon,ios         # Full mobile pipeline
#   ./build-all-apps.sh aab,amazon,ios,windows # All platforms including Windows
#   ./build-all-apps.sh windows                # Windows only
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default platforms
PLATFORMS="${1:-aab}"

# All casino game apps in LuckyJackpotCasino org
APPS=(
  "kenocasino"
  "blackjack21"
  "videopokercasino"
  "multihandpoker"
  "keno4card"
  "keno20card"
  "kenosuper4x"
  "roulette"
  "vintageslots"
)

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🤖 BuildBot 9000 - Batch Build All Apps${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Platforms:${NC} $PLATFORMS"
echo -e "${GREEN}Apps:${NC} ${#APPS[@]}"
echo ""

# Confirm before triggering
read -p "$(echo -e ${YELLOW}Trigger ${#APPS[@]} builds? [y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

echo ""
echo "🚀 Triggering builds..."
echo ""

BUILD_IDS=()

for APP in "${APPS[@]}"; do
  echo -e "${BLUE}Triggering:${NC} $APP..."
  
  # Map app names to workflow filenames
  case $APP in
    "kenocasino") WORKFLOW="keno-builds.yml" ;;
    "blackjack21") WORKFLOW="blackjack-builds.yml" ;;
    *) WORKFLOW="${APP}-builds.yml" ;;
  esac
  
  gh workflow run $WORKFLOW \
    --repo LuckyJackpotCasino/$APP \
    --field build_platforms=$PLATFORMS 2>&1
  
  if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Queued"
    
    # Get the build ID (latest run)
    sleep 2
    BUILD_ID=$(gh run list --repo LuckyJackpotCasino/$APP --limit 1 --json databaseId --jq '.[0].databaseId')
    BUILD_IDS+=("$APP:$BUILD_ID")
  else
    echo -e "  ${RED}✗${NC} Failed to trigger"
  fi
  
  echo ""
  sleep 1  # Rate limiting
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All ${#APPS[@]} builds triggered!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Monitor builds:"
for BUILD in "${BUILD_IDS[@]}"; do
  APP="${BUILD%%:*}"
  ID="${BUILD##*:}"
  echo "  $APP: https://github.com/LuckyJackpotCasino/$APP/actions/runs/$ID"
done
echo ""
echo "Or watch all at once:"
echo "  https://github.com/LuckyJackpotCasino/kenocasino/actions"
echo ""
echo -e "${YELLOW}Tip:${NC} Use './build-all-apps.sh aab' for quick SDK testing (AAB only)"
echo -e "${YELLOW}Tip:${NC} Use './build-all-apps.sh windows' for Windows Store builds only"
echo ""

