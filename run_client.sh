#!/bin/bash -xe

venv=${VENV:-$HOME/venv/hyperapp}

. $venv/bin/activate

# export LOG_CFG="${LOG_CFG-client-file}"

rm /tmp/client*.log || true

cd $(dirname $0)

./client.py "$@"

# tail -n500 /tmp/client-info.log
