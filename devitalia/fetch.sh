#!/usr/bin/env bash

set -e

SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}
DEVITALIA_DATADIR=${DEVITALIA_DATADIR:-SCRIPTDIR/devitalia/data}
DEVITALIA_NUM_THREADS=${DEVITALIA_NUM_THREADS:-10}
DEVITALIA_TOKEN_GITHUB=${DEVITALIA_TOKEN_GITHUB:-unset}
DEVITALIA_TEAMID_SLACK=${DEVITALIA_TEAMID_SLACK:-unset}
DEVITALIA_TOKEN_SLACK=${DEVITALIA_TOKEN_SLACK:-unset}
DEVITALIA_FORUM_API_KEY=${DEVITALIA_FORUM_API_KEY:-unset}
DEVITALIA_GOOGLE_WPID=${DEVITALIA_GOOGLE_WPID:-unset}
DEVITALIA_GOOGLE_PROJECT_ID=${DEVITALIA_GOOGLE_PROJECT_ID:-unset}
DEVITALIA_GOOGLE_PRIVATE_ID=${DEVITALIA_GOOGLE_PRIVATE_ID:-unset}
DEVITALIA_GOOGLE_PRIVATE_KEY=${DEVITALIA_GOOGLE_PRIVATE_KEY:-unset}
DEVITALIA_GOOGLE_CLIENT_EMAIL=${DEVITALIA_GOOGLE_CLIENT_EMAIL:-unset}
DEVITALIA_GOOGLE_CLIENT_ID=${DEVITALIA_GOOGLE_CLIENT_ID:-unset}
DEVITALIA_GOOGLE_CLIENT_X509_CERT_URL=${DEVITALIA_GOOGLE_CLIENT_X509_CERT_URL:-unset}

if [ "${DEVITALIA_TOKEN_GITHUB}" == "unset" ]; then
  echo "ERROR: must specify a GitHub token."
  exit 1
fi

if [ "${DEVITALIA_TEAMID_SLACK}" == "unset" ]; then
  echo "ERROR: must specify a Slack team ID."
  exit 1
fi

if [ "${DEVITALIA_TOKEN_SLACK}" == "unset" ]; then
  echo "ERROR: must specify a Slack APP token."
  exit 1
fi

if [ "${DEVITALIA_FORUM_API_KEY}" == "unset" ]; then
  echo "ERROR: must specify a Forum token."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_WPID}" == "unset" ]; then
  echo "ERROR: must specify a Google WPID."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_PROJECT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google project ID."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_PRIVATE_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google private ID."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_PRIVATE_KEY}" == "unset" ]; then
  echo "ERROR: must specify a Google private key."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_CLIENT_EMAIL}" == "unset" ]; then
  echo "ERROR: must specify a Google client email."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_CLIENT_ID}" == "unset" ]; then
  echo "ERROR: must specify a Google client ID."
  exit 1
fi

if [ "${DEVITALIA_GOOGLE_CLIENT_X509_CERT_URL}" == "unset" ]; then
  echo "ERROR: must specify a Google client x509 cert url."
  exit 1
fi

python3 ${SCRIPTDIR}/devitalia/fetch-engines/main.py \
    --data_dir "${DEVITALIA_DATADIR}" \
    --num_threads "${DEVITALIA_NUM_THREADS}" \
    --token_github "${DEVITALIA_TOKEN_GITHUB}" \
    --teamid_slack "${DEVITALIA_TEAMID_SLACK}" \
    --token_slack "${DEVITALIA_TOKEN_SLACK}" \
    --forum_api_key "${DEVITALIA_FORUM_API_KEY}" \
    --google_wpid "${DEVITALIA_GOOGLE_WPID}" \
    --google_project_id "${DEVITALIA_GOOGLE_PROJECT_ID}" \
    --google_private_id "${DEVITALIA_GOOGLE_PRIVATE_ID}" \
    --google_private_key "${DEVITALIA_GOOGLE_PRIVATE_KEY}" \
    --google_client_email "${DEVITALIA_GOOGLE_CLIENT_EMAIL}" \
    --google_client_id "${DEVITALIA_GOOGLE_CLIENT_ID}" \
    --google_client_x509_cert_url "${DEVITALIA_GOOGLE_CLIENT_X509_CERT_URL}"
