#!/usr/bin/env bash

# install the REST API and CLI

KOSTYOR_DIR=$(pwd)

export KOSTYOR_PORT=5000

python setup.py install

if ! [ -d /tmp/kostyor-cli ]; then
    cd /tmp
    git clone https://github.com/sc68cal/Kostyor-cli.git
else
    git -C /tmp/kostyor-cli pull
fi

cd /tmp/kostyor-cli

python /tmp/kostyor-cli/setup.py install

# Start the REST API

cd $KOSTYOR_DIR

python kostyor/rest_api.py &

sleep 5

kostyor cluster-list

kostyor cluster-status TEST

pkill -f 'python kostyor/rest_api.py'
