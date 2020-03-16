#!/usr/bin/env bash

set -e

echo "<run cie>"

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
CIE_DATADIR=${CIE_DATADIR:-SCRIPTDIR/data/cie}
CIE_ENV=${CIE_ENV:-unset}
CIE_STATS_URL=${CIE_STATS_URL:-unset}
MONGODB_HOSTNAME=${MONGODB_HOSTNAME:-unset}
MONGODB_DATABASE=${MONGODB_DATABASE:-unset}
MONGODB_USERNAME=${MONGODB_USERNAME:-unset}
MONGODB_PASSWORD=${MONGODB_PASSWORD:-unset}
MONGODB_AUTHDB=${MONGODB_AUTHDB:-admin}

if [ "${CIE_ENV}" = "unset" ]; then
  echo "ERROR: must specify the env."
  exit 1
fi
if [ "${CIE_DATADIR}" = "unset" ]; then
  echo "ERROR: must specify a data dir."
  exit 1
fi
if [ "${CIE_STATS_URL}" = "unset" ]; then
  echo "ERROR: must specify a csv stats url."
  exit 1
fi

if [ "${MONGODB_HOSTNAME}" = "unset" ]; then
  echo "ERROR: must specify a mongo host."
  exit 1
fi
if [ "${MONGODB_DATABASE}" = "unset" ]; then
  echo "ERROR: must specify a mongo database name."
  exit 1
fi

if [ "${MONGODB_USERNAME}" = "unset" ]; then
  echo "ERROR: must specify a mongo db user."
  exit 1
fi
if [ "${MONGODB_PASSWORD}" = "unset" ]; then
  echo "ERROR: must specify a mongo database password."
  exit 1
fi

python3 ${SCRIPTDIR}/cie/main.py \
    --env "${CIE_ENV}" \
    --data-dir "${CIE_DATADIR}" \
    --stats-url "${CIE_STATS_URL}" \
    --mongodb-host "${MONGODB_HOSTNAME}" \
    --mongodb-db "${MONGODB_DATABASE}" \
    --mongodb-user "${MONGODB_USERNAME}" \
    --mongodb-pass "${MONGODB_PASSWORD}" \
    --mongodb-authdb "${MONGODB_AUTHDB}"

echo "</run cie>"
