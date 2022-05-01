#!/bin/bash -xe

venv=${VENV:-$HOME/venv/hyperapp}

source $venv/bin/activate

cd "$( dirname "$0" )"

./construct_resources.py "$@"
