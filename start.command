#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ "$(uname -s)" == Darwin ]]; then
  poc_venv="$HOME/Library/Application Support/LayaDecisionLab/venv"
else
  poc_venv="$PWD/.venv"
fi
poc_hash="$(shasum -a 256 requirements.lock.txt | cut -d ' ' -f 1)"
if [[ ! -x "$poc_venv/bin/python" ]]; then
  echo 'First run: preparing the isolated Python environment…'
  if command -v python3.11 >/dev/null; then poc_python="$(command -v python3.11)"; else poc_python="$(command -v python3)"; fi
  "$poc_python" -m venv --copies "$poc_venv"
fi
if [[ ! -f "$poc_venv/requirements.sha256" ]] || [[ "$(cat "$poc_venv/requirements.sha256")" != "$poc_hash" ]]; then
  "$poc_venv/bin/python" -m pip install -r requirements.lock.txt
  printf '%s\n' "$poc_hash" > "$poc_venv/requirements.sha256"
fi
export HF_HOME="$PWD/.cache/huggingface"
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TOKENIZERS_PARALLELISM=false
printf '\nLaya Decision Lab: http://127.0.0.1:8765\nKeep this terminal open. Press Ctrl+C to stop.\n\n'
exec "$poc_venv/bin/python" -m uvicorn app:app --host 127.0.0.1 --port 8765
