#!/bin/bash -xe

venv=${VENV:-$HOME/.venv-hyperapp-3.9.2}

. $venv/bin/activate

# Hack/fix for https://bugreports.qt.io/browse/QTCREATORBUG-24967
# ~/.venv-hyperapp-3.9.2/lib/python3.9/site-packages/PySide2/Qt/plugins/platforms$
# > ln -s /usr/lib/x86_64-linux-gnu/libxcb-util.so.0.0.0 libxcb-util.so.1
export LD_LIBRARY_PATH="$HOME/.venv-hyperapp-3.9.2/lib/python3.9/site-packages/PySide2/Qt/plugins/platforms"

export LOG_CFG=client-file

rm /tmp/client*.log || true

cd $(dirname $0)

./client.py

tail -n500 /tmp/client-info.log
