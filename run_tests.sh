#!/bin/bash -e

DIR=$(dirname $0)
if [ "$1" == "fast" ]; then
	shift
	ARGS=( "-m" "not slow" "$@" )
else
	ARGS=( "$@" )
fi

cd $DIR
set -x
PYTHONPATH=$PYTHONPATH:$DIR ~/venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}"
