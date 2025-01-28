#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}

export LOG_CFG="${LOG_CFG:-client}"

source "$venv/bin/activate"

rm /tmp/client*.log || true

cd "$( dirname "$0" )"

set -x

time ./boot.py base,rc,common,ui,models,views,sample,lcs,client client_main "$@"

# tail -n500 /tmp/client-info.log
