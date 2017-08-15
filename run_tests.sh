#!/bin/bash -e

DIR=$(dirname $0)

if [ "$1" == "fast" ]; then
	ARGS="-m not slow"
	shift
else
	ARGS=""
fi

cd $DIR
PYTHONPATH=$PYTHONPATH:$DIR ~/venv/bin/pytest --ignore dynamic_modules "$ARGS" "$@"
