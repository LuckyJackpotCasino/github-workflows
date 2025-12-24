#!/bin/bash
# Add concurrency control to all app workflow files

echo "🔒 Adding concurrency control to prevent parallel builds of the same app"
echo ""

apps=(
  "blackjack21"
  "keno4card"
  "keno20card"
  "kenocasino"
  "kenosuper4x"
  "roulette"
  "vintageslots"
  "videopokercasino"
  "multihandpoker"
  "fvg-multicardkeno"
  "fvg-keno"
  "fvg-fourcardkeno"
)

for app in "${apps[@]}"; do
  echo "Processing $app..."
  
  # Clone the repo temporarily
  temp_dir=$(mktemp -d)
  cd "$temp_dir"
  
  if ! git clone "git@github.com:LuckyJackpotCasino/${app}.git" . 2>/dev/null; then
    echo "  ❌ Failed to clone $app"
    cd -
    rm -rf "$temp_dir"
    continue
  fi
  
  # Find workflow files
  workflow_files=(.github/workflows/*-builds.yml)
  
  for workflow in "${workflow_files[@]}"; do
    if [ ! -f "$workflow" ]; then
      continue
    fi
    
    # Check if concurrency already exists
    if grep -q "^concurrency:" "$workflow"; then
      echo "  ✓ Already has concurrency control"
    else
      echo "  📝 Adding concurrency control to $workflow"
      
      # Add concurrency after the 'on:' section
      # This is a simplified approach - insert after line with 'on:'
      awk '
        /^on:/ {
          print
          print ""
          print "concurrency:"
          print "  group: ${{ github.workflow }}-${{ github.ref }}"
          print "  cancel-in-progress: true  # Cancel old builds when new one starts"
          next
        }
        {print}
      ' "$workflow" > "${workflow}.tmp" && mv "${workflow}.tmp" "$workflow"
      
      # Commit the change
      git add "$workflow"
      git commit -m "Add concurrency control to prevent parallel builds" || true
    fi
  done
  
  # Push changes
  if git diff --quiet HEAD origin/master 2>/dev/null; then
    echo "  ✓ No changes needed"
  else
    echo "  ⬆️  Pushing changes..."
    git push origin master
    echo "  ✅ Done"
  fi
  
  cd -
  rm -rf "$temp_dir"
  echo ""
done

echo "✅ Concurrency control added to all apps!"
echo ""
echo "Now when you trigger a build:"
echo "  - If another build is queued/running, it will be cancelled"
echo "  - Only the newest build will run"
echo "  - No more parallel builds of the same app!"

