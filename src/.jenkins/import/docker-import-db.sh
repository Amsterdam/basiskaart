#!/usr/bin/env bash

set -u   # crash on missing environment variables
set -e   # stop on any error
set -x   # log every command.

source /.jenkins-import/docker-wait.sh

echo "GOB Objectstore container: $OBJECTSTORE_ENV"

# load data in database
python /app/import_basiskaart.py
