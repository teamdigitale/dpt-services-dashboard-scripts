#!/usr/bin/env bash

set -e

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
PADIGITALE_DATADIR=${PADIGITALE_DATADIR:-SCRIPTDIR/padigitale/data}
MONGODB_HOSTNAME=${MONGODB_HOSTNAME:-unset}
MONGODB_DATABASE=${MONGODB_DATABASE:-unset}
MONGODB_USERNAME=${MONGODB_USERNAME:-unset}
MONGODB_PASSWORD=${MONGODB_PASSWORD:-unset}
MONGODB_AUTHDB=${MONGODB_AUTHDB:-metabase}

if [ "${MONGODB_HOSTNAME}" = "unset" ]; then
  echo "ERROR: must specify a mongo host."
  exit 1
fi

if [ "${MONGODB_DATABASE}" = "unset" ]; then
  echo "ERROR: must specify a mongo database name."
  exit 1
fi

if [ "${MONGODB_USERNAME}" = "unset" ]; then
  echo "ERROR: must specify a mongo user name."
  exit 1
fi

if [ "${MONGODB_PASSWORD}" = "unset" ]; then
  echo "ERROR: must specify a mongo pass."
  exit 1
fi

python3 ${SCRIPTDIR}/padigitale/main.py \
    --data-dir "${PADIGITALE_DATADIR}" \
    --mongodb-host "${MONGODB_HOSTNAME}" \
    --mongodb-db "${MONGODB_DATABASE}" \
    --mongodb-user "${MONGODB_USERNAME}" \
    --mongodb-pass "${MONGODB_PASSWORD}" \
    --mongodb-authdb "${MONGODB_AUTHDB}"
