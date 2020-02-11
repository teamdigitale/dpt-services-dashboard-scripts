#!/bin/env sh

set -e

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
DEVITALIA_DATADIR=${DEVITALIA_DATADIR:-/var/opt/devitalia}
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

cd ${SCRIPTDIR} && python devitalia/devitalia.py \
    --data-dir "${DEVITALIA_DATADIR}" \
    --mongodb-host "${MONGODB_HOST}" \
    --mongodb-db "${MONGODB_DB}" \
    --mongodb-user "${MONGODB_DB_USER}" \
    --mongodb-pass "${MONGODB_DB_PASS}" \
    --mongodb-authdb "${MONGODB_DB_AUTHDB}"
