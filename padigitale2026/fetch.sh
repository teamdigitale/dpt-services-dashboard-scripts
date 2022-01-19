#!/usr/bin/env bash

set -e

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
PADIGITALE_DATADIR=${PADIGITALE_DATADIR:-SCRIPTDIR/padigitale/data}
PADIGITALE_NUM_THREADS=${PADIGITALE_NUM_THREADS:-10}
PADIGITALE_TOKEN_MAILGUN=${PADIGITALE_TOKEN_MAILGUN:-unset}
PADIGITALE_GOOGLE_WPID=${PADIGITALE_GOOGLE_WPID:-unset}
PADIGITALE_GOOGLE_PROJECT_ID=${PADIGITALE_GOOGLE_PROJECT_ID:-unset}
PADIGITALE_GOOGLE_PRIVATE_ID=${PADIGITALE_GOOGLE_PRIVATE_ID:-unset}
PADIGITALE_GOOGLE_PRIVATE_KEY=${PADIGITALE_GOOGLE_PRIVATE_KEY:-unset}
PADIGITALE_GOOGLE_CLIENT_EMAIL=${PADIGITALE_GOOGLE_CLIENT_EMAIL:-unset}
PADIGITALE_GOOGLE_CLIENT_ID=${PADIGITALE_GOOGLE_CLIENT_ID:-unset}
PADIGITALE_GOOGLE_CLIENT_X509_CERT_URL=${PADIGITALE_GOOGLE_CLIENT_X509_CERT_URL:-unset}

if [ "${PADIGITALE_TOKEN_MAILGUN}" == "unset" ]; then
  echo "ERROR: must specify a Mailgun token."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_WPID}" == "unset" ]; then
  echo "ERROR: must specify a Google WPID."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_PROJECT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google project ID."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_PRIVATE_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google private ID."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_PRIVATE_KEY}" == "unset" ]; then
  echo "ERROR: must specify a Google private key."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_CLIENT_EMAIL}" == "unset" ]; then
  echo "ERROR: must specify a Google client email."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_CLIENT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google client ID."
  exit 1
fi

if [ "${PADIGITALE_GOOGLE_CLIENT_X509_CERT_URL}" == "unset" ]; then
  echo "ERROR: must specify a Google client x509 cert url."
  exit 1
fi

python3 ${SCRIPTDIR}/padigitale2026/fetch-engines/main.py \
    --data_dir "${PADIGITALE_DATADIR}" \
    --num_threads "${PADIGITALE_NUM_THREADS}" \
    --token_mailgun "${PADIGITALE_TOKEN_MAILGUN}" \
    --google_wpid "${PADIGITALE_GOOGLE_WPID}" \
    --google_project_id "${PADIGITALE_GOOGLE_PROJECT_ID}" \
    --google_private_id "${PADIGITALE_GOOGLE_PRIVATE_ID}" \
    --google_private_key "${PADIGITALE_GOOGLE_PRIVATE_KEY}" \
    --google_client_email "${PADIGITALE_GOOGLE_CLIENT_EMAIL}" \
    --google_client_id "${PADIGITALE_GOOGLE_CLIENT_ID}" \
    --google_client_x509_cert_url "${PADIGITALE_GOOGLE_CLIENT_X509_CERT_URL}"
