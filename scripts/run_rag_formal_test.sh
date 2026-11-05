#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export NLTK_DATA="${NLTK_DATA:-$HOME/nltk_data}"
export TOKENIZERS_PARALLELISM=false
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
MASTER="${1:-outputs/rag_formal_20261105_v2}"
FEATURES="${2:-outputs/rag_formal_development_20261105_v1}"
CONFIG="${3:-configs/rag_formal.yaml}"
RUN_DIR="$MASTER/partitions/test"
TEST_OUTPUT="$FEATURES/final_test"
PYTHON="$PWD/.venv/bin/python"
mkdir -p "$RUN_DIR/logs"
trap 'printf "{\"exit_code\":%s}\n" "$?" > "$RUN_DIR/pipeline_exit.json"' EXIT
"$PYTHON" - "$MASTER" "$CONFIG" <<'PY'
import json,sys,shutil
from pathlib import Path
sys.path.insert(0,'src')
from rag_hd.formal_gate import validate_test_freeze
from rag_hd.io import file_sha256,load_config
master=Path(sys.argv[1]);run=master/'partitions/test';dev=master/'partitions/development'
validate_test_freeze(run)
preflight=json.loads((master/'preflight.json').read_text())
if preflight['partitions']['test']['prepared_sha256']!=file_sha256(run/'prepared.jsonl'):
    raise ValueError('Final test inputs changed after preparation')
if json.loads((run/'config.json').read_text())!=load_config(Path(sys.argv[2])):
    raise ValueError('Test configuration changed')
for filename,digest in preflight['inference_implementation'].items():
    if file_sha256(Path(filename))!=digest:raise ValueError('Frozen inference implementation changed')
if json.loads((dev/'config.json').read_text())!=json.loads((run/'config.json').read_text()):
    raise ValueError('Development/test model configurations differ')
probe=json.loads((dev/'deployment_probe.json').read_text())
if not probe['passed']:raise ValueError('Require successful training-only resource probe')
if not (run/'deployment_probe.json').exists():
    shutil.copy2(dev/'deployment_probe.json',run/'deployment_probe.json')
    (run/'probe_reuse.json').write_text(json.dumps({'source':str(dev/'deployment_probe.json'),
        'source_sha256':file_sha256(dev/'deployment_probe.json'),
        'probe_inputs':'development_train_only','new_test_probe_calls':0},indent=2)+'\n')
elif file_sha256(run/'deployment_probe.json')!=file_sha256(dev/'deployment_probe.json'):
    raise ValueError('Copied deployment probe changed')
print('Freeze verified; running final 120 inputs. Training-only probe reused.',flush=True)
PY
"$PYTHON" -m pip check > "$RUN_DIR/logs/dependencies.log"
"$PYTHON" -m pip freeze > "$RUN_DIR/requirements.lock.txt"
for stage in generate score evaluate; do
  "$PYTHON" scripts/rag_prototype.py --stage "$stage" --config "$CONFIG" --run-dir "$RUN_DIR" 2>&1 | tee "$RUN_DIR/logs/$stage.log"
done
"$PYTHON" scripts/extract_valid_evidence.py --run-dir "$RUN_DIR" --output-dir "$TEST_OUTPUT" 2>&1 | tee "$RUN_DIR/logs/features.log"
"$PYTHON" scripts/predict_formal_frozen.py --run-dir "$RUN_DIR" --model-dir "$FEATURES/formal_training" --output-dir "$TEST_OUTPUT" 2>&1 | tee "$RUN_DIR/logs/frozen_predictions.log"
