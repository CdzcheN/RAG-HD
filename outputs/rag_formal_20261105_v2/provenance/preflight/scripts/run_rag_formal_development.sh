#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
RUN_DIR="${1:-outputs/rag_formal_20261105_v2}"
CONFIG="${2:-configs/rag_formal.yaml}"
.venv/bin/python - "$RUN_DIR" "$CONFIG" <<'PY'
import json,sys
from pathlib import Path
sys.path.insert(0,'src')
from rag_hd.io import file_sha256,load_config
run=Path(sys.argv[1]); config=Path(sys.argv[2])
preflight=json.loads((run/'preflight.json').read_text())
if (not preflight['prepared_inputs_ready'] or
        preflight['prepared_sha256']!=file_sha256(run/'prepared.jsonl') or
        preflight['config_sha256']!=file_sha256(run/'config.json') or
        json.loads((run/'config.json').read_text())!=load_config(config)):
    raise ValueError('Formal input preflight/configuration changed')
for path,digest in preflight['inference_implementation'].items():
    if file_sha256(Path(path))!=digest:
        raise ValueError('Inference method changed after preflight')
development=run/'partitions/development'
if preflight['partitions']['development']['prepared_sha256']!=file_sha256(development/'prepared.jsonl'):
    raise ValueError('Development partition changed')
print('Verified 480 development inputs. Final 120 test inputs remain held out.')
PY
exec bash scripts/run_rag_challenges.sh "$RUN_DIR/partitions/development" "$CONFIG"
