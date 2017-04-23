DIR=$(dirname $0)
cd $DIR
PYTHONPATH=$PYTHONPATH:$DIR ~/venv/bin/pytest --ignore dynamic_modules "$@"
