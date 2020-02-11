#!/bin/env sh

set -e

echo "<run cie>"

CIE_ENV=${CIE_ENV:-unset}
CIE_DATADIR=${CIE_DATADIR:-/var/opt/cie}
SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
MONGODB_HOST=${MONGODB_HOST:-unset}
MONGODB_DB=${MONGODB_DB:-unset}
MONGODB_DB_USER=${MONGODB_DB_USER:-unset}
MONGODB_DB_PASS=${MONGODB_DB_PASS:-unset}
MONGODB_DB_AUTHDB=${MONGODB_DB_AUTHDB:-admin}

if [ "${CIE_ENV}" = "unset" ]; then
  echo "ERROR: must specify the env."
  exit 1
fi
if [ "${CIE_DATADIR}" = "unset" ]; then
  echo "ERROR: must specify a data dir."
  exit 1
fi

if [ "${MONGODB_HOST}" = "unset" ]; then
  echo "ERROR: must specify a mongo host."
  exit 1
fi
if [ "${MONGODB_DB}" = "unset" ]; then
  echo "ERROR: must specify a mongo database name."
  exit 1
fi

if [ "${MONGODB_DB_USER}" = "unset" ]; then
  echo "ERROR: must specify a mongo db user."
  exit 1
fi
if [ "${MONGODB_DB_PASS}" = "unset" ]; then
  echo "ERROR: must specify a mongo database password."
  exit 1
fi

cd ${SCRIPTDIR} && python "${SCRIPTDIR}/cie/cie.py" \
    --env "${CIE_ENV}" \
    --data-dir "${CIE_DATADIR}" \
    --mongodb-host "${MONGODB_HOST}" \
    --mongodb-db "${MONGODB_DB}" \
    --mongodb-user "${MONGODB_DB_USER}" \
    --mongodb-pass "${MONGODB_DB_PASS}" \
    --mongodb-authdb "${MONGODB_DB_AUTHDB}"

echo "</run cie>"
