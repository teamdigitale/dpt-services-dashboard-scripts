#!/usr/bin/env python3

import requests
import yaml

from .engine import Engine


class CatalogoRegioni(Engine):
    """
    Class that computes the statistics from the reuse catalog from Developers Italia.

    Example of results:
    # python main.py -t catalogoregioni
        regione,num_pas,num_softwares
        Abruzzo,0,0
        Basilicata,0,0
    """

    API_BASE_URL = "https://api.developers.italia.it/v1"
    INDICEPA_URL = "https://www.indicepa.gov.it/public-services/opendata-read-service.php?dstype=FS&filename=amministrazioni.txt"

    regioni = [
        "Abruzzo",
        "Basilicata",
        "Calabria",
        "Campania",
        "Emilia-Romagna",
        "Friuli-Venezia Giulia",
        "Lazio",
        "Liguria",
        "Lombardia",
        "Marche",
        "Molise",
        "Piemonte",
        "Puglia",
        "Sardegna",
        "Sicilia",
        "Toscana",
        "Trentino-Alto Adige/Südtirol",
        "Umbria",
        "Valle d'Aosta/Vallée d'Aoste",
        "Veneto",
    ]

    software = []
    administrations = []

    def __init__(self, args):
        super(CatalogoRegioni, self).__init__(args, "catalogoregioni")
        self.keyname = "regione"
        # each metric must have a corresponding method
        self.metric_names = ["num_pas", "num_softwares"]

        for regione in self.regioni:
            self.metrics[regione] = {}
            for metric in self.metric_names:
                self.metrics[regione][metric] = 0

    def _get_software(self):
        items = []

        page = True
        page_after = ""

        while page:
            res = requests.get(f"{API_BASE_URL}/software?&{page_after}")
            res.raise_for_status()

            body = res.json()
            items += body["data"]

            page_after = body["links"]["next"]
            if page_after:
                # Remove the '?'
                page_after = page_after[1:]

            page = bool(page_after)

        self.software = items

    def _get_administrations(self):
        pas = requests.get(self.INDICEPA_URL).content.decode("utf-8-sig").splitlines()

        self.administrations = []

        titles = pas[0].split("\t")
        for p in pas[1:]:
            arr = {}
            values = p.split("\t")
            for i in range(0, len(values)):
                arr[titles[i]] = values[i]
            self.administrations.append(arr)

    def num_pas(self):
        self.logger.info("Getting num PAs...")
        if not self.software:
            self._get_software()
        if not self.administrations:
            self._get_administrations()

        listpa = {}
        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            if (
                "it" in publiccode
                and "riuso" in sw["publiccode"]["it"]
                and "codiceIPA" in sw["publiccode"]["it"]["riuso"]
            ):
                newpa = sw["publiccode"]["it"]["riuso"]["codiceIPA"].lower()
                regione = None
                for a in self.administrations:
                    if a["cod_amm"].lower() == newpa:
                        regione = a["Regione"]

                if not regione:
                    continue
                if regione not in listpa:
                    listpa[regione] = []
                if newpa not in listpa[regione]:
                    listpa[regione].append(newpa)

        for reg, lst_pas in listpa.items():
            self.metrics[reg]["num_pas"] = len(lst_pas)

    def num_softwares(self):
        self.logger.info("Getting num softwares...")
        if not self.software:
            self._get_software()
        if not self.administrations:
            self._get_administrations()

        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            if (
                "it" in publiccode
                and "riuso" in sw["publiccode"]["it"]
                and "codiceIPA" in sw["publiccode"]["it"]["riuso"]
            ):
                newpa = sw["publiccode"]["it"]["riuso"]["codiceIPA"].lower()
                regione = None
                for a in self.administrations:
                    if a["cod_amm"].lower() == newpa:
                        regione = a["Regione"]

                if not regione:
                    continue
                self.metrics[regione]["num_softwares"] += 1
