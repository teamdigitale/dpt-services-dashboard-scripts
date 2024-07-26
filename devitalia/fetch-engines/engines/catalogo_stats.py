#!/usr/bin/env python3

from datetime import datetime
from statistics import mean

import requests
import yaml

from .engine import Engine

API_BASE_URL = "https://api.developers.italia.it/v1"


class Catalogo(Engine):
    """
    Class that computes the statistics from the reuse catalog from Developers Italia.

    Example of results:
    # python main.py -t catalogo
        timestamp,num_pas,num_softwares,vitality
        2017-04-15T00:00:00Z,1,3,46.63333333333333
    """

    software = []

    def __init__(self, args):
        super(Catalogo, self).__init__(args, "catalogo")
        # each metric must have a corresponding method
        self.metric_names = [
            "num_pas",
            "num_softwares",
            "num_softwares_reuse",
            "num_softwares_reusing",
            "vitality",
            "num_pas_reusing",
        ]

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

    # Total number of PAs
    def num_pas(self):
        self.logger.info("Getting num repos...")
        if not self.software:
            self._get_software()

        totpa = []
        listpa = {}
        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            # FIXME: non è la data corretta, da prendere da repolist
            timestamp = self.strip_date(publiccode["releaseDate"])
            if timestamp not in listpa:
                listpa[timestamp] = []

            ipa = publiccode.get("it", {}).get("riuso", {}).get("codiceIPA", "")
            if ipa:
                newpa = ipa.lower()
                if newpa not in listpa[timestamp] and newpa not in totpa:
                    listpa[timestamp].append(newpa)
                    totpa.append(newpa)

        for ts, lst_pas in listpa.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]["num_pas"] = len(lst_pas)

    # Total number of softwares
    def num_softwares(self):
        self.logger.info("Getting num softwares...")
        if not self.software:
            self._get_software()

        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            timestamp = self.strip_date(publiccode["releaseDate"])
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]["num_softwares"] += 1

    # Total number of softwares released for reuse
    def num_softwares_reuse(self):
        self.logger.info("Getting num softwares reuse...")
        if not self.software:
            self._get_software()

        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            timestamp = self.strip_date(publiccode["releaseDate"])
            self.add_timestamp_to_metrics(timestamp)
            if publiccode.get("it", {}).get("riuso", {}).get("codiceIPA", False):
                self.metrics[timestamp]["num_softwares_reuse"] += 1

    # Total number of softwares reused at least once
    def num_softwares_reusing(self):
        self.logger.info("Getting num softwares reusing...")
        if not self.software:
            self._get_software()

        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            timestamp = self.strip_date(publiccode["releaseDate"])
            self.add_timestamp_to_metrics(timestamp)
            if publiccode.get("usedBy", ""):
                self.metrics[timestamp]["num_softwares_reusing"] += 1

    # Total software vitality
    def vitality(self):
        self.logger.info("Getting software vitality...")
        if not self.software:
            self._get_software()

        vitality = {}
        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            timestamp = self.strip_date(publiccode["releaseDate"])
            if timestamp not in vitality:
                vitality[timestamp] = {"num": 0, "val": 0}

            vitality[timestamp]["num"] += 1
            if sw["vitalityDataChart"] is None:
                vitality[timestamp]["val"] += 0
            else:
                vitality[timestamp]["val"] += mean(sw["vitalityDataChart"])

        for ts, vit in vitality.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]["vitality"] = vit["val"] / vit["num"]

    # Total number of PAs reusing software
    def num_pas_reusing(self):
        self.logger.info("Getting num reusing pas...")
        if not self.software:
            self._get_software()

        listpa = {}
        pa_seen = []
        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            # FIXME: non è la data corretta, da prendere da repolist
            timestamp = self.strip_date(publiccode["releaseDate"])
            if timestamp not in listpa:
                listpa[timestamp] = []

            if "usedBy" in publiccode:
                for pa in publiccode["usedBy"]:
                    if (
                        pa.lower() not in listpa[timestamp]
                        and pa.lower() not in pa_seen
                    ):
                        listpa[timestamp].append(pa.lower())
                        pa_seen.append(pa.lower())

        for ts, lst_pas in listpa.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]["num_pas_reusing"] = len(lst_pas)
