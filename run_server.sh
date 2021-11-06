#!/bin/bash -xe

venv=${VENV:-$HOME/venv/hyperapp}

source $venv/bin/activate

cd "$( dirname "$0" )"

$HOME/bin/autoreload.py -f '*.types' -f '*.yaml' -f '*.py'  . ./server.py
