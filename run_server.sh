#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}

export LOG_CFG="${LOG_CFG:-server}"

source $venv/bin/activate

cd "$( dirname "$0" )"

$HOME/bin/autoreload.py -f '*.types' -f '*.yaml' -f '*.py'  . ./boot.py base,common,ui,models,sample,server server_main
