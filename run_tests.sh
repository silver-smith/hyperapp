#!/bin/bash -e

DIR=$(dirname $0)
venv=${VENV:-$HOME/venv/hyperapp}

FILTER="$DIR/scripts/log-sort.py"

cd $DIR

export PYTHONPATH=$PYTHONPATH:$DIR

set -x

#$venv/bin/pytest "$@" | "$FILTER"
time $venv/bin/pytest --ignore-glob='*.dyn.py' "$@"
