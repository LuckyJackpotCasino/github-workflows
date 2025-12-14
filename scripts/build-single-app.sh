#!/bin/bash
#
# BuildBot 9000 - Build Single App
#
# Triggers a build for a specific app
# Usage:
#   ./build-single-app.sh <app-name> [platforms]
#
# Examples:
#   ./build-single-app.sh kenocasino aab
#   ./build-single-app.sh blackjack21 aab,amazon,ios
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check arguments
if [ $# -lt 1 ]; then
  echo -e "${RED}Usage:${NC} $0 <app-name> [platforms]"
  echo ""
  echo "Available apps:"
  echo "  kenocasino, blackjack21, videopokercasino, multihandpoker,"
  echo "  keno4card, keno20card, kenosuper4x, roulette, vintageslots"
  echo ""
  echo "Examples:"
  echo "  $0 kenocasino aab"
  echo "  $0 blackjack21 aab,amazon,ios"
  exit 1
fi

APP=$1
PLATFORMS="${2:-aab,amazon,ios}"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🤖 BuildBot 9000 - Build $APP${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}App:${NC} $APP"
echo -e "${GREEN}Platforms:${NC} $PLATFORMS"
echo ""

# Map app names to workflow filenames
case $APP in
  "kenocasino") WORKFLOW="keno-builds.yml" ;;
  "blackjack21") WORKFLOW="blackjack-builds.yml" ;;
  *) WORKFLOW="${APP}-builds.yml" ;;
esac

# Trigger the build
echo "🚀 Triggering build..."
gh workflow run $WORKFLOW \
  --repo LuckyJackpotCasino/$APP \
  --field build_platforms=$PLATFORMS

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Build queued!${NC}"
  echo ""
  
  # Wait a moment and get build ID
  sleep 3
  BUILD_ID=$(gh run list --repo LuckyJackpotCasino/$APP --limit 1 --json databaseId --jq '.[0].databaseId')
  
  echo "Monitor at:"
  echo "  https://github.com/LuckyJackpotCasino/$APP/actions/runs/$BUILD_ID"
  echo ""
  echo "Or watch with:"
  echo "  gh run watch $BUILD_ID --repo LuckyJackpotCasino/$APP"
  echo ""
else
  echo -e "${RED}✗ Failed to trigger build${NC}"
  exit 1
fi

