#!/bin/bash -e

venv=${VENV:-$HOME/venv/hyperapp}

export LOG_CFG="${LOG_CFG:-server}"

source $venv/bin/activate

cmd=(
  ./boot.py
  base,rc,common,ui,models,sample,server
  server_main
  )

cd "$( dirname "$0" )"

if [[ "$1" == "-a" ]]; then
  shift
  $HOME/bin/autoreload.py -f '*.types' -f '*.yaml' -f '*.py'  . "${cmd[@]}"
else
  "${cmd[@]}"
fi

