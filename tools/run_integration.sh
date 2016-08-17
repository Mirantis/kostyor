#!/usr/bin/env bash

set -e

# install the REST API and CLI

KOSTYOR_DIR=$(pwd)

export KOSTYOR_PORT=5000

python setup.py install

if ! [ -d /tmp/kostyor-cli ]; then
    cd /tmp
    git clone https://github.com/sc68cal/Kostyor-cli.git
else
    git -C /tmp/Kostyor-cli pull
fi

cd /tmp/Kostyor-cli

python /tmp/Kostyor-cli/setup.py install

# Start the REST API

cd $KOSTYOR_DIR

python kostyor/rest_api.py &

sleep 5

kostyor cluster-list

kostyor cluster-status TEST

pkill -f 'python kostyor/rest_api.py'
