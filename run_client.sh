#!/bin/bash -xe

venv=${VENV:-$HOME/venv}

. $venv/bin/activate

export LOG_CFG=client-file

rm /tmp/client*.log

cd $(dirname $0)

./run_client.py

tail -n500 /tmp/client-info.log
