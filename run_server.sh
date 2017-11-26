#!/bin/bash -xe

. $HOME/venv/bin/activate

cd $(dirname $0)

killall python3 || true

watch_mask_list=(
	*.py
	hyperapp/common/htypes/*.py
	hyperapp/common/*.py
	hyperapp/common/interface/*.types
	hyperapp/server/*.py
	hyperapp/server/*.dyn.py
	hyperapp/server/*.yaml
	dynamic_modules/*
)

autoreload.sh "${watch_mask_list[*]}" ./run_server.py server.identity.pem
