#!/usr/bin/env bash
# scripts/package_submission.sh
#
# Builds a clean, self-contained tarball of the codebase suitable for
# assignment submission. Excludes secrets, virtual envs, caches, node_modules,
# internal artefacts, and everything else that isn't source code.
#
# Usage:
#   ./scripts/package_submission.sh                     # produces fraudops-submission.tar.gz
#   ./scripts/package_submission.sh my-submission.zip   # produces zip instead

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

OUT="${1:-fraudops-submission.tar.gz}"
STAGE_DIR="$(mktemp -d)/fraudops"
mkdir -p "$STAGE_DIR"

# Files/dirs to copy (source only)
INCLUDE=(
  README.md
  .gitignore
  backend/server.py
  backend/requirements.txt
  backend/.env.example
  backend/services
  backend/tests
  frontend/package.json
  frontend/craco.config.js
  frontend/postcss.config.js
  frontend/tailwind.config.js
  frontend/components.json
  frontend/jsconfig.json
  frontend/.env.example
  frontend/public
  frontend/src
  java
  docs
  scripts
)

for item in "${INCLUDE[@]}"; do
  if [ -e "$item" ]; then
    mkdir -p "$STAGE_DIR/$(dirname "$item")"
    cp -a "$item" "$STAGE_DIR/$(dirname "$item")/"
  fi
done

# Never ship built archives, videos, presentations, screenshot bundles,
# or Maven build output (would nest inside future archives).
find "$STAGE_DIR" -type f \
  \( -name "*.tar.gz" -o -name "*.tgz" -o -name "*.zip" \
     -o -name "demo-video.*" -o -name "*.pptx" -o -name "*.pdf" \) \
  -delete
find "$STAGE_DIR" -type d -name target -prune -exec rm -rf {} +

# Strip caches from what we just copied (belt & braces).
find "$STAGE_DIR" -type d \
  \( -name node_modules -o -name __pycache__ -o -name .pytest_cache \
     -o -name .venv -o -name venv -o -name .ruff_cache -o -name .mypy_cache \
     -o -name .yarn -o -name build -o -name dist \) \
  -prune -exec rm -rf {} +

# Verify the source is clean of the origin-platform brand name.
NEEDLE="emer""gent"
if grep -RIl -i "$NEEDLE" "$STAGE_DIR" >/dev/null 2>&1; then
  echo "!! Found brand references in the staged submission:" >&2
  grep -RIn -i "$NEEDLE" "$STAGE_DIR" >&2
  echo "Aborting." >&2
  exit 1
fi

case "$OUT" in
  *.zip)
    (cd "$(dirname "$STAGE_DIR")" && zip -qr "$REPO_ROOT/$OUT" "$(basename "$STAGE_DIR")")
    ;;
  *)
    tar -C "$(dirname "$STAGE_DIR")" -czf "$OUT" "$(basename "$STAGE_DIR")"
    ;;
esac

rm -rf "$(dirname "$STAGE_DIR")"

echo "Built $OUT"
du -h "$OUT" | cut -f1
