# Trigger and Verify All Builds

## Quick Start

Open your terminal and run:

```bash
cd ~/Documents/BuildBot1000/github-workflows/scripts
./build-all-apps.sh aab
```

Or trigger manually:

## Manual Trigger (One by One)

```bash
# Blackjack21
gh workflow run blackjack-builds.yml --repo LuckyJackpotCasino/blackjack21 --field build_platforms=aab

# Keno4card
gh workflow run keno4card-builds.yml --repo LuckyJackpotCasino/keno4card --field build_platforms=aab

# Keno20card  
gh workflow run keno20card-builds.yml --repo LuckyJackpotCasino/keno20card --field build_platforms=aab

# Kenocasino
gh workflow run keno-builds.yml --repo LuckyJackpotCasino/kenocasino --field build_platforms=aab

# KenoSuper4x
gh workflow run kenosuper4x-builds.yml --repo LuckyJackpotCasino/kenosuper4x --field build_platforms=aab

# Roulette
gh workflow run roulette-builds.yml --repo LuckyJackpotCasino/roulette --field build_platforms=aab

# VintageSlots
gh workflow run vintageslots-builds.yml --repo LuckyJackpotCasino/vintageslots --field build_platforms=aab

# VideoPokerCasino
gh workflow run videopokercasino-builds.yml --repo LuckyJackpotCasino/videopokercasino --field build_platforms=aab

# MultiHandPoker
gh workflow run multihandpoker-builds.yml --repo LuckyJackpotCasino/multihandpoker --field build_platforms=aab
```

## Monitor All Builds

```bash
# Watch all build statuses
for app in blackjack21 keno4card keno20card kenocasino kenosuper4x roulette vintageslots videopokercasino multihandpoker; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📱 $app"
  gh run list --repo LuckyJackpotCasino/$app --limit 3
  echo ""
done
```

## Update Status Table

After builds complete, check results and update the README:

1. Check build status for each app
2. Update the "Build Health" column in README.md:
   - ✅ Passing - if build succeeded
   - ⚠️ Warning - if some platforms failed
   - ❌ Failing - if build failed
3. Add timestamp to "Last Updated"
4. Commit and push changes

```bash
cd /tmp/github-workflows
git pull
# Edit README.md with build status
git add README.md
git commit -m "Update build status - $(date '+%Y-%m-%d')"
git push
```

## Direct Links to Actions

- [blackjack21](https://github.com/LuckyJackpotCasino/blackjack21/actions)
- [keno4card](https://github.com/LuckyJackpotCasino/keno4card/actions)
- [keno20card](https://github.com/LuckyJackpotCasino/keno20card/actions)
- [kenocasino](https://github.com/LuckyJackpotCasino/kenocasino/actions)
- [kenosuper4x](https://github.com/LuckyJackpotCasino/kenosuper4x/actions)
- [roulette](https://github.com/LuckyJackpotCasino/roulette/actions)
- [vintageslots](https://github.com/LuckyJackpotCasino/vintageslots/actions)
- [videopokercasino](https://github.com/LuckyJackpotCasino/videopokercasino/actions)
- [multihandpoker](https://github.com/LuckyJackpotCasino/multihandpoker/actions)
