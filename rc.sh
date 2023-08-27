#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}

source $venv/bin/activate

cd "$( dirname "$0" )"

set -x

time ./rc.py --rpc-timeout=5 "$@"
