#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export NLTK_DATA="${NLTK_DATA:-$HOME/nltk_data}"
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
RUN_DIR="${1:-outputs/rag_challenge_20261104_v4}"
CONFIG="${2:-configs/rag_challenge.yaml}"
mkdir -p "$RUN_DIR/logs"
trap 'printf "{\"exit_code\":%s}\n" "$?" > "$RUN_DIR/pipeline_exit.json"' EXIT
PYTHON="$PWD/.venv/bin/python"
"$PYTHON" -m pip check > "$RUN_DIR/logs/dependencies.log"
"$PYTHON" -m pip freeze > "$RUN_DIR/requirements.lock.txt"
git rev-parse HEAD > "$RUN_DIR/source_revision.txt"
if [[ ! -f "$RUN_DIR/data_manifest.json" ]]; then
  "$PYTHON" scripts/rag_prototype.py --stage prepare --config "$CONFIG" --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/logs/prepare.log"
fi
for stage in probe generate score evaluate; do
  "$PYTHON" scripts/rag_prototype.py --stage "$stage" --config "$CONFIG" --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/logs/$stage.log"
done
