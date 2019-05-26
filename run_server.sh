#!/bin/bash -xe

venv=${VENV:-$HOME/venv}

. $venv/bin/activate

cd $(dirname $0)

killall python3 || true

# using python autoreload script:
#   https://gist.github.com/jmingtan/1171288

$HOME/bin/autoreload.py -f '*.types' -f '*.yaml' -f '*.py'  . ./run_server.py server.identity.pem
