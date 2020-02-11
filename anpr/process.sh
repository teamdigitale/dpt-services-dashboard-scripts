#!/bin/env sh

set -e

MAPS_APIKEY=${MAPS_APIKEY:-unset}
DAF_APIKEY=${DAF_APIKEY:-unset}
DRYRUN=${DRYRUN:-no}
DATADIR=${DATADIR:-/var/opt/anpr}
SCRIPTDIR=${SCRIPTDIR:-/opt/ingestion_scripts}

dryrunflag=
if [ "x${DRYRUN}" == "xyes" ]; then
  dryrunflag="--dry-run"
fi

cd ${SCRIPTDIR} && python "${SCRIPTDIR}/anpr/anpr.py" \
    --daf-apikey "${DAF_APIKEY}" \
    --maps-apikey "${MAPS_APIKEY}" \
    --maps-cache "${SCRIPTDIR}/anpr/maps_cache.json" \
    --comuni-subentrati "${DATADIR}/ComuniSubentrati.xml" \
    --comuni-presubentro "${DATADIR}/ComuniPresubentro.xml" \
    --anomalie "${DATADIR}/AnomalieSchedeSoggettoPreSub.xml" \
    --anomalie-ag-entrate "${DATADIR}/AnomalieAESchedeSoggettoPreSub.xml" \
    --piano-subentro "${DATADIR}/pianosubentro.csv" \
    $dryrunflag
