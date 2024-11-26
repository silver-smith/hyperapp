#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}
root_dir="$( dirname "$0" )"
source $venv/bin/activate

cd "$root_dir"

set -x

ipython --profile-dir=$root_dir/ipython-profile "$@"
# ipython --profile=hyperapp -i ./ipython_init.py "$@"
