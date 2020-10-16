#!/bin/bash

set -e -o pipefail

mkdir -p /tmp/outputs/high_security
mkdir -p /tmp/outputs/medium_security

touch db.sqlite3

docker-compose build --build-arg pythonversion=3.8.1
docker-compose up
