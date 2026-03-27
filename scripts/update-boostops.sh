#!/bin/bash
#
# BuildBot 9000 - Update BoostOps Submodule Across All Apps
#
# Updates the BoostOps submodule pointer in all app repos via GitHub API.
# No cloning required - uses the Git Data API to update the tree directly.
#
# Usage:
#   ./update-boostops.sh                    # Update to latest BoostOps main
#   ./update-boostops.sh <commit-sha>       # Update to specific commit
#   ./update-boostops.sh --dry-run          # Preview what would change
#   ./update-boostops.sh --dry-run <sha>    # Preview with specific commit
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

ORG="LuckyJackpotCasino"
BOOSTOPS_REPO="BoostOps/boostops-shared"
SUBMODULE_PATH="Assets/BoostOps"

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

DRY_RUN=false
TARGET_SHA=""

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    *) TARGET_SHA="$arg" ;;
  esac
done

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  BuildBot 9000 - Update BoostOps Submodule${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ -z "$TARGET_SHA" ]; then
  echo -e "${CYAN}Fetching latest BoostOps commit from main...${NC}"
  TARGET_SHA=$(gh api "repos/$BOOSTOPS_REPO/commits/main" --jq '.sha')
fi

TARGET_SHORT="${TARGET_SHA:0:8}"
TARGET_MSG=$(gh api "repos/$BOOSTOPS_REPO/commits/$TARGET_SHA" --jq '.commit.message | split("\n")[0]')

echo -e "${GREEN}Target BoostOps:${NC} $TARGET_SHORT - $TARGET_MSG"
echo ""

if $DRY_RUN; then
  echo -e "${YELLOW}DRY RUN - No changes will be made${NC}"
  echo ""
fi

UPDATED=0
SKIPPED=0
FAILED=0

for APP in "${APPS[@]}"; do
  echo -ne "${BLUE}$APP${NC}: "

  CURRENT_SHA=$(gh api "repos/$ORG/$APP/contents/$SUBMODULE_PATH" --jq '.sha' 2>/dev/null || echo "NOT_FOUND")

  if [ "$CURRENT_SHA" = "NOT_FOUND" ]; then
    echo -e "${RED}submodule not found${NC}"
    FAILED=$((FAILED + 1))
    continue
  fi

  if [ "$CURRENT_SHA" = "$TARGET_SHA" ]; then
    echo -e "${GREEN}already up to date${NC} (${CURRENT_SHA:0:8})"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  echo -ne "${CURRENT_SHA:0:8} -> ${TARGET_SHORT} "

  if $DRY_RUN; then
    echo -e "${YELLOW}[would update]${NC}"
    UPDATED=$((UPDATED + 1))
    continue
  fi

  DEFAULT_BRANCH=$(gh api "repos/$ORG/$APP" --jq '.default_branch')
  BRANCH_SHA=$(gh api "repos/$ORG/$APP/git/refs/heads/$DEFAULT_BRANCH" --jq '.object.sha')
  COMMIT_TREE=$(gh api "repos/$ORG/$APP/git/commits/$BRANCH_SHA" --jq '.tree.sha')

  NEW_TREE=$(gh api "repos/$ORG/$APP/git/trees" \
    --method POST \
    --field "base_tree=$COMMIT_TREE" \
    --input <(echo "{\"tree\":[{\"path\":\"$SUBMODULE_PATH\",\"mode\":\"160000\",\"type\":\"commit\",\"sha\":\"$TARGET_SHA\"}]}") \
    --jq '.sha')

  NEW_COMMIT=$(gh api "repos/$ORG/$APP/git/commits" \
    --method POST \
    --field "message=Update BoostOps to $TARGET_SHORT ($TARGET_MSG)" \
    --field "tree=$NEW_TREE" \
    --field "parents[]=$BRANCH_SHA" \
    --jq '.sha')

  gh api "repos/$ORG/$APP/git/refs/heads/$DEFAULT_BRANCH" \
    --method PATCH \
    --field "sha=$NEW_COMMIT" > /dev/null

  echo -e "${GREEN}updated${NC}"
  UPDATED=$((UPDATED + 1))

  sleep 0.5
done

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
if $DRY_RUN; then
  echo -e "${YELLOW}DRY RUN SUMMARY:${NC}"
else
  echo -e "${GREEN}UPDATE SUMMARY:${NC}"
fi
echo -e "  Updated: $UPDATED  |  Skipped: $SKIPPED  |  Failed: $FAILED"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
