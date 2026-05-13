#!/bin/bash
set -e

service postgresql start
sleep 3

export PSYCOPG_TEST_DSN="host=127.0.0.1 user=postgres password=password dbname=postgres"

if [ $# -eq 0 ]; then
    pytest tests/
else
    IFS=',' read -ra FILES <<< "$1"
    pytest "${FILES[@]}"
fi
