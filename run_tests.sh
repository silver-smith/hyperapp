#!/bin/bash -e

DIR=$(dirname $0)
if [ "$1" == "full" ]; then
	shift
	ARGS=( "$@" )
else
	ARGS=( "-m" "not slow" "$@" )
fi

cd $DIR
set -x
PYTHONPATH=$PYTHONPATH:$DIR ~/venv/bin/pytest --ignore dynamic_modules "${ARGS[@]}"
