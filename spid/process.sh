#!/bin/env sh

set -e

echo "<run spid>"

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
SPID_DATADIR=${SPID_DATADIR:-SCRIPTDIR/data/spid}
MONGODB_HOSTNAME=${MONGODB_HOSTNAME:-unset}
MONGODB_DATABASE=${MONGODB_DATABASE:-unset}
MONGODB_USERNAME=${MONGODB_USERNAME:-unset}
MONGODB_PASSWORD=${MONGODB_PASSWORD:-unset}
MONGODB_AUTHDB=${MONGODB_AUTHDB:-admin}

if [ "${MONGODB_HOSTNAME}" = "unset" ]; then
  echo "ERROR: must specify a mongo host."
  exit 1
fi
if [ "${MONGODB_DATABASE}" = "unset" ]; then
  echo "ERROR: must specify a mongo database name."
  exit 1
fi

python "${SCRIPTDIR}/spid/main.py" \
    --data-path-dest "${SPID_DATADIR}" \
    --mongodb-host "${MONGODB_HOSTNAME}" \
    --mongodb-db "${MONGODB_DATABASE}" \
    --mongodb-user "${MONGODB_USERNAME}" \
    --mongodb-pass "${MONGODB_PASSWORD}" \
    --mongodb-authdb "${MONGODB_AUTHDB}"

echo "</run spid>"
