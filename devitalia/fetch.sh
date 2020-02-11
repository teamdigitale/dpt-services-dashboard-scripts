#!/bin/env sh

set -e

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
DEVITALIA_DATADIR=${DEVITALIA_DATADIR:-/var/opt/devitalia}
NUM_THREADS=${NUM_THREADS:-10}
TOKEN_GITHUB=${TOKEN_GITHUB:-unset}
TOKEN_SLACK=${TOKEN_SLACK:-unset}
FORUM_API_KEY=${FORUM_API_KEY:-unset}
GOOGLE_WPID=${GOOGLE_WPID:-unset}
GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID:-unset}
GOOGLE_PRIVATE_ID=${GOOGLE_PRIVATE_ID:-unset}
GOOGLE_PRIVATE_KEY=${GOOGLE_PRIVATE_KEY:-unset}
GOOGLE_CLIENT_EMAIL=${GOOGLE_CLIENT_EMAIL:-unset}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-unset}
GOOGLE_CLIENT_X509_CERT_URL=${FORUM_API_KEY:-unset}

if [ "${TOKEN_GITHUB}" == "unset" ]; then
  echo "ERROR: must specify a GitHub token."
  exit 1
fi

if [ "${TOKEN_SLACK}" == "unset" ]; then
  echo "ERROR: must specify a Slack token."
  exit 1
fi

if [ "${FORUM_API_KEY}" == "unset" ]; then
  echo "ERROR: must specify a Forum token."
  exit 1
fi

if [ "${GOOGLE_PROJECT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google project ID."
  exit 1
fi

if [ "${GOOGLE_PRIVATE_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google private ID."
  exit 1
fi

if [ "${GOOGLE_CLIENT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google client ID."
  exit 1
fi

cd ${SCRIPTDIR}/devitalia && python fetch-engines/main.py -w \
    --data_dir "${DEVITALIA_DATADIR}" \
    --num_threads "${NUM_THREADS}" \
    --token_github "${TOKEN_GITHUB}" \
    --token_slack "${TOKEN_SLACK}" \
    --forum_api_key "${FORUM_API_KEY}" \
    --google_wpid "${GOOGLE_WPID}" \
    --google_project_id "${GOOGLE_PROJECT_ID}" \
    --google_private_id "${GOOGLE_PRIVATE_ID}" \
    --google_private_key "${GOOGLE_PRIVATE_KEY}" \
    --google_client_email "${GOOGLE_CLIENT_EMAIL}" \
    --google_client_id "${GOOGLE_CLIENT_ID}" \
    --google_client_x509_cert_url "${GOOGLE_CLIENT_X509_CERT_URL}"
