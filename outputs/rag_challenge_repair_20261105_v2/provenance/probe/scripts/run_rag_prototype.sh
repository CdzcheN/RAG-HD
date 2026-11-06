#!/usr/bin/env bash
# Pinned local development pilot. No API server or external inference provider.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export NLTK_DATA="${NLTK_DATA:-$HOME/nltk_data}"
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONUNBUFFERED=1
RUN_DIR="${1:-outputs/rag_prototype_20261104}"
mkdir -p "$RUN_DIR/logs"
PYTHON="$PWD/.venv/bin/python"
"$PYTHON" -m pip check | tee "$RUN_DIR/logs/dependencies.log"
"$PYTHON" -m pip freeze > "$RUN_DIR/requirements.lock.txt"
git rev-parse HEAD > "$RUN_DIR/source_revision.txt"
for stage in prepare probe generate score evaluate; do
  "$PYTHON" scripts/rag_prototype.py --stage "$stage" --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/logs/$stage.log"
done
