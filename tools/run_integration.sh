#!/usr/bin/env bash

set -e

# install the REST API and CLI

KOSTYOR_DIR=$(pwd)

export KOSTYOR_PORT=5000

python setup.py install

if ! [ -d /tmp/Kostyor-cli ]; then
    cd /tmp
    git clone https://github.com/sc68cal/Kostyor-cli.git
else
    git -C /tmp/Kostyor-cli pull
fi

cd /tmp/Kostyor-cli

python /tmp/Kostyor-cli/setup.py install

# Use Alembic to build up the database
alembic -c $KOSTYOR_DIR/kostyor/db/migrations/alembic.ini upgrade head

python $KOSTYOR_DIR/tools/create_initial_data.py

# Start the REST API

cd $KOSTYOR_DIR

python kostyor/rest_api.py &

sleep 5

kostyor cluster-list

CLUSTER_ID=$(kostyor cluster-list -f value -c 'Cluster ID' | tail -n 1)

kostyor cluster-status $CLUSTER_ID

kostyor list-upgrade-versions

kostyor list-discovery-methods

pkill -f 'python kostyor/rest_api.py'
