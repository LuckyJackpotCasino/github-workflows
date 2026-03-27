#!/bin/bash
#
# BuildBot 9000 - Bump App Version (patch increment)
#
# Increments the patch version (x.y.Z -> x.y.Z+1) in Unity ProjectSettings
# via the GitHub API. No cloning required.
#
# Usage:
#   ./bump-version.sh kenocasino              # Bump kenocasino patch version
#   ./bump-version.sh kenocasino 2.0.0        # Set kenocasino to specific version
#   ./bump-version.sh --all                   # Bump all apps that have ProjectSettings
#   ./bump-version.sh --check                 # Show current versions without changing
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ORG="LuckyJackpotCasino"
PS_PATH="ProjectSettings/ProjectSettings.asset"

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

bump_patch() {
  local ver=$1
  local major minor patch
  IFS='.' read -r major minor patch <<< "$ver"
  patch=$((patch + 1))
  echo "${major}.${minor}.${patch}"
}

get_version() {
  local app=$1
  local content sha

  local response=$(gh api "repos/$ORG/$app/contents/$PS_PATH" 2>/dev/null || echo "")
  if [ -z "$response" ] || echo "$response" | grep -q '"message"' 2>/dev/null; then
    echo ""
    return
  fi

  echo "$response" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
content = base64.b64decode(data['content']).decode('utf-8')
for line in content.split('\n'):
    if 'bundleVersion:' in line:
        print(line.split('bundleVersion:')[1].strip())
        break
"
}

set_version() {
  local app=$1
  local new_ver=$2

  local response=$(gh api "repos/$ORG/$app/contents/$PS_PATH" 2>/dev/null)
  local file_sha=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['sha'])")
  local content=$(echo "$response" | python3 -c "
import sys, json, base64
data = json.load(sys.stdin)
print(base64.b64decode(data['content']).decode('utf-8'))
")

  local updated=$(echo "$content" | python3 -c "
import sys, re
content = sys.stdin.read()
content = re.sub(r'(bundleVersion: )[\d.]+', r'\g<1>$new_ver', content, count=1)
print(content, end='')
")

  local encoded=$(echo "$updated" | base64)

  local default_branch=$(gh api "repos/$ORG/$app" --jq '.default_branch' 2>/dev/null)

  gh api "repos/$ORG/$app/contents/$PS_PATH" \
    --method PUT \
    --field "message=Bump version to $new_ver" \
    --field "content=$encoded" \
    --field "sha=$file_sha" \
    --field "branch=$default_branch" \
    --jq '.commit.sha' 2>&1
}

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  BuildBot 9000 - Version Manager${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

CHECK_ONLY=false
BUMP_ALL=false
TARGET_APP=""
TARGET_VER=""

for arg in "$@"; do
  case $arg in
    --check) CHECK_ONLY=true ;;
    --all) BUMP_ALL=true ;;
    [0-9]*.[0-9]*.[0-9]*) TARGET_VER="$arg" ;;
    *) TARGET_APP="$arg" ;;
  esac
done

if [ -z "$TARGET_APP" ] && ! $BUMP_ALL && ! $CHECK_ONLY; then
  echo -e "${YELLOW}Usage:${NC}"
  echo "  $0 <app-name>              # Bump patch version (x.y.Z+1)"
  echo "  $0 <app-name> <version>    # Set specific version"
  echo "  $0 --all                   # Bump all apps"
  echo "  $0 --check                 # Show current versions"
  exit 1
fi

for APP in "${APPS[@]}"; do
  if [ -n "$TARGET_APP" ] && [ "$APP" != "$TARGET_APP" ]; then
    continue
  fi

  CURRENT=$(get_version "$APP")

  if [ -z "$CURRENT" ]; then
    if $CHECK_ONLY || $BUMP_ALL; then
      echo -e "${BLUE}$APP${NC}: ${YELLOW}no ProjectSettings${NC}"
    fi
    continue
  fi

  if $CHECK_ONLY; then
    echo -e "${BLUE}$APP${NC}: $CURRENT"
    continue
  fi

  if [ -n "$TARGET_VER" ]; then
    NEW_VER="$TARGET_VER"
  else
    NEW_VER=$(bump_patch "$CURRENT")
  fi

  echo -ne "${BLUE}$APP${NC}: $CURRENT -> $NEW_VER "

  RESULT=$(set_version "$APP" "$NEW_VER")
  if [ $? -eq 0 ] && echo "$RESULT" | grep -q '[a-f0-9]'; then
    echo -e "${GREEN}done${NC} (${RESULT:0:8})"
  else
    echo -e "${RED}failed${NC} - $RESULT"
  fi
done

echo ""
