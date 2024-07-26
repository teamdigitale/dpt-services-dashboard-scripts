#!/usr/bin/env python3

import requests
import yaml

from .engine import Engine


class CatalogoAudiences(Engine):
    """
    Class that computes the statistics from the reuse catalog from Developers Italia.

    Example of results:
    # python main.py -t catalogoaudiences
        slug,software_audiences
        <software_id>_1,government
        <software_id>_2,local-authorities
        <software_id>_3,research
    """

    API_BASE_URL = "https://api.developers.italia.it/v1"

    software = []

    def __init__(self, args):
        super(CatalogoAudiences, self).__init__(args, "catalogoaudiences")
        self.keyname = "slug"
        # each metric must have a corresponding method
        self.metric_names = ["software_audiences"]

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

    def software_audiences(self):
        self.logger.info("Getting software audiences...")
        if not self.software:
            self._get_software()

        for sw in self.software:
            publiccode = {}
            try:
                publiccode = yaml.safe_load(sw["publiccodeYml"])
            except:
                continue

            audience = publiccode.get("intendedAudience", {}).get("scope", [])

            i = 1
            for a in audience:
                swid = "%s_%d" % (sw["id"], i)
                self.add_timestamp_to_metrics(swid)
                self.metrics[swid]["software_audiences"] = a
                i += 1
