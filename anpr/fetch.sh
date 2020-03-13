#!/usr/bin/env bash 

datadir=${DATADIR:-/var/cache/dashboard_scripts/anpr}
files_to_download="
AnomalieAESchedeSoggettoPreSub.xml
AnomalieSchedeSoggettoPreSub.xml
AnomalieSchedeSoggettoPreSubV.2.xml
ComuniPresubentro.xml
ComuniSubentrati.xml
OperazioniPreSub_2017.xml
OperazioniTest_2017.xml
DatiCheckListV3.2.xml
DatiCheckListV3.3.xml
"

print_exit_msg() {
  >&2 echo "Please, provide a valid $1"
  exit 1
}

if [ -z "$BASE_URL" ]; then
  print_exit_msg "BASE_URL"
elif [ -z "$ANPR_DASHBOARD_APIKEY" ]; then
  print_exit_msg "ANPR_DASHBOARD_APIKEY"
elif [ -z "$SHARE_ID" ]; then
  print_exit_msg "SHARE_ID"
fi

invite="${BASE_URL}/?share=${SHARE_ID}"
dl_pre="${BASE_URL}/webdav/share/${SHARE_ID}"
dl_post="?dl=true"

for file in ${files_to_download}; do
  cookie_store=$(mktemp)
  curl -s -c ${cookie_store} "$invite" > /dev/null
  curl -f -s -b ${cookie_store} -o "${datadir}/${file}" "${dl_pre}/${file}${dl_post}"

  if [ $? -ne 0 ]; then
    echo "Failed to download ${file}"
  fi

  rm ${cookie_store}
done

curl -f -s -o "${datadir}/pianosubentro.csv" -H "APIKey: ${ANPR_DASHBOARD_APIKEY}" 'https://dashboard.anpr.it/downloadpianosubentro?detailed_records=true'

if [ $? -ne 0 ]; then
  echo "Failed to download pianosubentro.csv"
fi
