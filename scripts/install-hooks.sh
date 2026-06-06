#!/bin/sh
set -e

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit

echo "Git hooks installed (.githooks/pre-commit runs pytest before each commit)."
