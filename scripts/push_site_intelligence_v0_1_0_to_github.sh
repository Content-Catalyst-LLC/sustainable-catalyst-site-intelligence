#!/usr/bin/env bash
set -euo pipefail

ZIP_NAME="sustainable-catalyst-site-intelligence-v0.1.0-repo.zip"
REPO_DIR="sustainable-catalyst-site-intelligence-repo"
DEFAULT_REPO_URL=""

cd "$HOME/Downloads"

if [ ! -f "$ZIP_NAME" ]; then
  echo "Could not find $HOME/Downloads/$ZIP_NAME"
  echo "Download $ZIP_NAME into your Downloads folder, then run this script again."
  exit 1
fi

rm -rf "$REPO_DIR"
unzip -q "$ZIP_NAME" -d "$REPO_DIR"
cd "$REPO_DIR"

if [ ! -d .git ]; then
  git init
  git branch -M main
fi

git add .
git commit -m "Initial Sustainable Catalyst Site Intelligence v0.1.0" || true

if ! git remote get-url origin >/dev/null 2>&1; then
  if [ -z "$DEFAULT_REPO_URL" ]; then
    echo "No origin remote is set. Add one with:"
    echo "git remote add origin https://github.com/YOUR-USER/sustainable-catalyst-site-intelligence.git"
    exit 0
  fi
  git remote add origin "$DEFAULT_REPO_URL"
fi

git push -u origin main
