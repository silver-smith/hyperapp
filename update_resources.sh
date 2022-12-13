#!/bin/bash -xe

venv=${VENV:-$HOME/venv/hyperapp}

source $venv/bin/activate

cd "$( dirname "$0" )"

./update_resources.py "$@"
