#!/usr/bin/env bash

# install the REST API and CLI

python setup.py install

python kostyor/cli/setup.py install

# Start the REST API

screen -S kostyor -d -m python kostyor/rest_api.py


screen -X -S kostyor quit
