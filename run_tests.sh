#!/bin/bash -e

DIR=$(dirname $0)
venv=${VENV:-$HOME/venv}

if [ "$1" == "full" ]; then
	shift
	ARGS=( "$@" )
else
	ARGS=( "-m" "not slow" "$@" )
fi

FILTER="$DIR/scripts/log-sort.py"

cd $DIR
set -x
PYTHONPATH=$PYTHONPATH:$DIR $venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}" | "$FILTER"
