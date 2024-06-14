#!/usr/bin/env python3

import requests
import yaml

from .engine import Engine


class Onboarding(Engine):
    """
    Class that computes the statistics from the onboarding process for the reuse catalog from Developers Italia.

    Example of results:
    # python main.py -t onboarding
        timestamp,num_pas,num_pas_with_softwares
        2019-05-01T00:00:00Z,1,1
    """

    """
    Relevant files:
    - https://crawler.developers.italia.it/softwares.yml
    - https://crawler.developers.italia.it/amministrazioni.yml
    - https://crawler.developers.italia.it/software_categories.yml
    - https://crawler.developers.italia.it/software-open-source.yml
    - https://crawler.developers.italia.it/software-riuso.yml
    - https://crawler.developers.italia.it/software_scopes.yml
    - https://crawler.developers.italia.it/software_tags.yml
    """

    REPO_LIST = "https://onboarding.developers.italia.it/repo-list"
    SOFTWARES_URL = "https://crawler.developers.italia.it/softwares.yml"

    pas = None
    softwares = None
    administrations = None

    def __init__(self, args):
        super(Onboarding, self).__init__(args, "onboarding")
        # each metric must have a corresponding method
        self.metric_names = ["num_pas", "num_pas_with_softwares"]

    def _get_pas(self):
        sws = requests.get(self.REPO_LIST).content
        sws = yaml.safe_load(sws)
        self.pas = sws["registrati"]

    def _get_softwares(self):
        sws = requests.get(self.SOFTWARES_URL).content
        sws = yaml.safe_load(sws)
        self.softwares = sws

    def num_pas(self):
        self.logger.info("Getting num pas...")
        if self.pas is None:
            self._get_pas()

        for pa in self.pas:
            if "timestamp" in pa:
                timestamp = self.strip_date(pa["timestamp"])
            else:
                timestamp = self.strip_date("2019-05-01T00:00:00.000Z")

            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]["num_pas"] += 1

    def num_pas_with_softwares(self):
        self.logger.info("Getting num pas with software...")
        if self.pas is None:
            self._get_pas()

        if self.softwares is None:
            self._get_softwares()

        for pa in self.pas:
            if "timestamp" in pa:
                timestamp = self.strip_date(pa["timestamp"])
            else:
                timestamp = self.strip_date("2019-05-01T00:00:00.000Z")

            self.add_timestamp_to_metrics(timestamp)

            countpa = False
            for sw in self.softwares:
                if (
                    "it" in sw["publiccode"]
                    and "riuso" in sw["publiccode"]["it"]
                    and "codiceIPA" in sw["publiccode"]["it"]["riuso"]
                ):
                    if (
                        pa["ipa"].lower()
                        == sw["publiccode"]["it"]["riuso"]["codiceIPA"].lower()
                    ):
                        countpa = True

            if countpa:
                self.metrics[timestamp]["num_pas_with_softwares"] += 1
