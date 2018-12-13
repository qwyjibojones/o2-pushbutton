#!/bin/bash
# This is an initialization script to make the docker-compose useable.

# Get the sanfrancisco data if necessary
if [[ ! -d ./sanfrancisco || -z "$(ls -A ./sanfrancisco)" ]]; then
    echo "The imagery directory is missing or empty, so we'll fill it"
    if [[ ! -e ./sanfrancisco.tgz ]]; then
        echo "The sanfrancisco.tgz file is missing, pulling..."
        wget "https://s3.amazonaws.com/o2-test-data/sanfrancisco.tgz"
    fi
    echo "Extracting sanfrancisco.tgz..."
    tar -xzf ./sanfrancisco.tgz
fi
echo "sanfrancisco done"

# Get the elevation data if necessary
if [[ ! -d ./elevation || -z "$(ls -A ./elevation)" ]]; then
    echo "The elevation directory is missing or empty, so we'll fill it"
    if [[ ! -e ./dted-elevation.tgz ]]; then
        echo "The dted-elevation.tgz file is missing, pulling..."
        wget "https://s3.amazonaws.com/o2-test-data/elevation/dted/dted-elevation.tgz"
    fi
    echo "Extracting dted-elevation.tgz..."
    tar -xzf ./dted-elevation.tgz
fi
echo "elevation done"

# Create empty database directories
for i in pg_commit_ts/ pg_dynshmem/ pg_replslot/ pg_serial/ pg_snapshots/ pg_stat/ pg_tblspc/ pg_twophase/ pgdata/pg_logical/snapshots/ pgdata/pg_logical/mappings/; do
    if [[ ! -d ./pgdata/$i ]]; then
        mkdir ./pgdata/$i
    fi
done
