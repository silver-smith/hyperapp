#!/bin/bash -e

DIR=$(dirname $0)
venv=${VENV:-$HOME/.venv-hyperapp-3.9.2}

if [ "$1" == "full" ]; then
	shift
	ARGS=( "$@" )
else
	ARGS=( "-m" "not slow" "$@" )
fi

FILTER="$DIR/scripts/log-sort.py"

# Hack/fix for https://bugreports.qt.io/browse/QTCREATORBUG-24967
# ~/.venv-hyperapp-3.9.2/lib/python3.9/site-packages/PySide2/Qt/plugins/platforms$
# > ln -s /usr/lib/x86_64-linux-gnu/libxcb-util.so.0.0.0 libxcb-util.so.1
export LD_LIBRARY_PATH="$HOME/.venv-hyperapp-3.9.2/lib/python3.9/site-packages/PySide2/Qt/plugins/platforms"

cd $DIR

export PYTHONPATH=$PYTHONPATH:$DIR

set -x

#$venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}" | "$FILTER"
time $venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}"
