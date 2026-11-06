#!/usr/bin/env bash
# Run on the GPU host after installing requirements-minicheck.txt and logging in.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PYTHON="$PWD/.venv/bin/python"
RUN_DIR="${1:-outputs/minicheck_$(date +%Y%m%d_%H%M%S)}"
if [[ -e "$RUN_DIR" ]]; then
  echo "Refusing to overwrite existing experiment: $RUN_DIR" >&2
  exit 1
fi
mkdir -p "$RUN_DIR/logs"
RUN_DIR="$(cd "$RUN_DIR" && pwd)"
export NLTK_DATA="${NLTK_DATA:-$HOME/nltk_data}"
export HF_HUB_CACHE="$PWD/.cache/minicheck/hub"
export PYTHONUNBUFFERED=1
DATA_REVISION=981dfd0bd8e58e7238a9ab92b2e6ea44bce918e4
CURRENT_STAGE=setup

finish() {
  local code=$?
  if [[ $code -eq 0 ]]; then
    echo "complete $(date --iso-8601=seconds)" > "$RUN_DIR/status.txt"
  else
    echo "failed stage=$CURRENT_STAGE exit=$code $(date --iso-8601=seconds)" > "$RUN_DIR/status.txt"
  fi
}
trap finish EXIT

run_stage() {
  local stage=$1
  shift
  CURRENT_STAGE=$stage
  echo "$stage $(date --iso-8601=seconds)" | tee "$RUN_DIR/status.txt"
  "$@" 2>&1 | tee "$RUN_DIR/logs/$stage.log"
}

run_stage dependencies "$PYTHON" -m pip check
"$PYTHON" -m pip freeze > "$RUN_DIR/requirements.lock.txt"
git rev-parse HEAD > "$RUN_DIR/source_revision.txt"
git diff --binary HEAD > "$RUN_DIR/source_changes.patch"
cp scripts/run_minicheck_reproduction.sh "$RUN_DIR/launcher.sh"
cp requirements-minicheck.txt "$RUN_DIR/requirements-minicheck.txt"
run_stage preflight "$PYTHON" - <<'PY'
import os
from pathlib import Path
import nltk
import torch
from huggingface_hub import HfApi

if not torch.cuda.is_available():
    raise SystemExit('CUDA is unavailable. Run this script on the GPU host.')
print('GPU:', torch.cuda.get_device_name(0), '; torch:', torch.__version__)
HfApi().auth_check(repo_id='lytang/LLM-AggreFact', repo_type='dataset')
print('LLM-AggreFact access OK')
os.umask(0o077)
Path(os.environ['NLTK_DATA']).mkdir(mode=0o700, parents=True, exist_ok=True)
for package in ('punkt', 'punkt_tab'):
    try:
        nltk.data.find('tokenizers/' + package)
    except LookupError:
        nltk.download(package, download_dir=os.environ['NLTK_DATA'], raise_on_error=True)
assert nltk.sent_tokenize('This is a test. It works.') == ['This is a test.', 'It works.']
PY
run_stage smoke "$PYTHON" scripts/reproduce_minicheck.py --task smoke \
  --batch-size 1 --local-model-files --output-dir "$RUN_DIR"
run_stage debug "$PYTHON" scripts/reproduce_minicheck.py --task benchmark \
  --limit 100 --batch-size 1 --local-model-files --dataset-revision "$DATA_REVISION" \
  --output-dir "$RUN_DIR/debug"
run_stage benchmark "$PYTHON" scripts/reproduce_minicheck.py --task benchmark \
  --batch-size 1 --local-model-files --dataset-revision "$DATA_REVISION" --output-dir "$RUN_DIR"
run_stage analysis "$PYTHON" scripts/analyze_minicheck.py --skip-plots \
  --benchmark-dir "$RUN_DIR/benchmark" --output-dir "$RUN_DIR/analysis"
