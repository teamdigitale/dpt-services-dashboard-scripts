#!/usr/bin/env bash

set -e

echo "<run repubblica-digitale>"

MONGODB_HOSTNAME=${MONGODB_HOSTNAME:-unset}
MONGODB_DATABASE=${MONGODB_DATABASE:-unset}
MONGODB_USERNAME=${MONGODB_USERNAME:-unset}
MONGODB_PASSWORD=${MONGODB_PASSWORD:-unset}
MONGODB_AUTHDB=${MONGODB_AUTHDB:-metabase}

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
REPDIG_GOOGLE_PROJECT_ID=${REPDIG_GOOGLE_PROJECT_ID:-unset}
REPDIG_GOOGLE_PRIVATE_ID=${REPDIG_GOOGLE_PRIVATE_ID:-unset}
REPDIG_GOOGLE_PRIVATE_KEY=${REPDIG_GOOGLE_PRIVATE_KEY:-unset}
REPDIG_GOOGLE_CLIENT_EMAIL=${REPDIG_GOOGLE_CLIENT_EMAIL:-unset}
REPDIG_GOOGLE_CLIENT_ID=${REPDIG_GOOGLE_CLIENT_ID:-unset}
REPDIG_GOOGLE_CLIENT_X509_CERT_URL=${REPDIG_GOOGLE_CLIENT_X509_CERT_URL:-unset}

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

if [ "${REPDIG_GOOGLE_PROJECT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google project ID."
  exit 1
fi

if [ "${REPDIG_GOOGLE_PRIVATE_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google private ID."
  exit 1
fi

if [ "${REPDIG_GOOGLE_PRIVATE_KEY}" == "unset" ]; then
  echo "ERROR: must specify a Google private key."
  exit 1
fi

if [ "${REPDIG_GOOGLE_CLIENT_EMAIL}" == "unset" ]; then
  echo "ERROR: must specify a Google client email."
  exit 1
fi

if [ "${REPDIG_GOOGLE_CLIENT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google client ID."
  exit 1
fi

if [ "${REPDIG_GOOGLE_CLIENT_X509_CERT_URL}" == "unset" ]; then
  echo "ERROR: must specify a Google client x509 cert url."
  exit 1
fi

python3 ${SCRIPTDIR}/repubblica-digitale/main.py \
    --mongodb-host "${MONGODB_HOSTNAME}" \
    --mongodb-db "${MONGODB_DATABASE}" \
    --mongodb-user "${MONGODB_USERNAME}" \
    --mongodb-pass "${MONGODB_PASSWORD}" \
    --mongodb-authdb "${MONGODB_AUTHDB}" \
    --google_project_id "${REPDIG_GOOGLE_PROJECT_ID}" \
    --google_private_id "${REPDIG_GOOGLE_PRIVATE_ID}" \
    --google_private_key "${REPDIG_GOOGLE_PRIVATE_KEY}" \
    --google_client_email "${REPDIG_GOOGLE_CLIENT_EMAIL}" \
    --google_client_id "${REPDIG_GOOGLE_CLIENT_ID}" \
    --google_client_x509_cert_url "${REPDIG_GOOGLE_CLIENT_X509_CERT_URL}"

echo "</run repubblica-digitale>"
