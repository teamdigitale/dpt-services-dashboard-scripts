#!/bin/env sh

set -e

echo "<run spid>"

SPID_DATADIR=${SPID_DATADIR:-/var/opt/spid}
SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
MONGODB_HOST=${MONGODB_HOST:-unset}
MONGODB_DB=${MONGODB_DB:-unset}
MONGODB_DB_USER=${MONGODB_DB_USER:-unset}
MONGODB_DB_PASS=${MONGODB_DB_PASS:-unset}
MONGODB_DB_AUTHDB=${MONGODB_DB_AUTHDB:-admin}

if [ "${MONGODB_HOST}" = "unset" ]; then
  echo "ERROR: must specify a mongo host."
  exit 1
fi
if [ "${MONGODB_DB}" = "unset" ]; then
  echo "ERROR: must specify a mongo database name."
  exit 1
fi

cd "${SCRIPTDIR}" && python "${SCRIPTDIR}/spid/spid.py" \
    --data-path-dest "${SPID_DATADIR}" \
    --mongodb-host "${MONGODB_HOST}" \
    --mongodb-db "${MONGODB_DB}" \
    --mongodb-user "${MONGODB_DB_USER}" \
    --mongodb-pass "${MONGODB_DB_PASS}" \
    --mongodb-authdb "${MONGODB_DB_AUTHDB}"

echo "</run spid>"
