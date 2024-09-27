#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}

export LOG_CFG="${LOG_CFG:-rc}"

source "$venv/bin/activate"

cd "$( dirname "$0" )"

set -x

time ./boot.py rc_main --timeout=7 "$@"
