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

export PYTHONPATH=$PYTHONPATH:$DIR

set -x

#$venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}" | "$FILTER"
time $venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}"
