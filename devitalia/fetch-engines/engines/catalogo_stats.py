#!/usr/bin/env python3

import requests
import yaml

from statistics import mean
from datetime import datetime
from .engine import Engine

class Catalogo(Engine):
    """
    Class that computes the statistics from the reuse catalog from Developers Italia.
    
    Example of results:
    # python main.py -t catalogo
        timestamp,num_pas,num_softwares,vitality
        2017-04-15T00:00:00Z,1,3,46.63333333333333
    """

    '''
    Relevant files:
    - https://crawler.developers.italia.it/softwares.yml
    - https://crawler.developers.italia.it/amministrazioni.yml
    - https://crawler.developers.italia.it/software_categories.yml
    - https://crawler.developers.italia.it/software-open-source.yml
    - https://crawler.developers.italia.it/software-riuso.yml
    - https://crawler.developers.italia.it/software_scopes.yml
    - https://crawler.developers.italia.it/software_tags.yml
    '''

    SOFTWARES_URL = 'https://crawler.developers.italia.it/softwares.yml'
    INDICEPA_URL = 'https://www.indicepa.gov.it/public-services/opendata-read-service.php?dstype=FS&filename=amministrazioni.txt'

    softwares = None
    administrations = None

    def __init__(self, args):
        super(Catalogo, self).__init__(args, 'catalogo')
        #each metric must have a corresponding method
        self.metric_names = ['num_pas', 'num_softwares', 'num_softwares_reuse', 'num_softwares_reusing', 'vitality', 'num_pas_reusing']

    def _get_softwares(self):
        sws = requests.get(self.SOFTWARES_URL).content
        sws = yaml.safe_load(sws)
        self.softwares = sws

    def num_pas(self):
        self.logger.info('Getting num repos...')
        if self.softwares is None:
            self._get_softwares()

        totpa = []
        listpa = {}
        for sw in self.softwares:
            # FIXME: non è la data corretta, da prendere da repolist
            timestamp = self.strip_date(sw['publiccode']['releaseDate']) 
            if timestamp not in listpa:
                listpa[timestamp] = []

            if 'it' in sw['publiccode'] and 'riuso' in sw['publiccode']['it'] and 'codiceIPA' in sw['publiccode']['it']['riuso']:
                newpa = sw['publiccode']['it']['riuso']['codiceIPA'].lower()
                if newpa not in listpa[timestamp] and newpa not in totpa:
                    listpa[timestamp].append(newpa)
                    totpa.append(newpa)

        for ts, lst_pas in listpa.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]['num_pas'] = len(lst_pas)

    def num_softwares(self):
        self.logger.info('Getting num softwares...')
        if self.softwares is None:
            self._get_softwares()

        for sw in self.softwares:
            timestamp = self.strip_date(sw['publiccode']['releaseDate'])
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]['num_softwares'] += 1

    def num_softwares_reuse(self):
        self.logger.info('Getting num softwares reuse...')
        if self.softwares is None:
            self._get_softwares()

        for sw in self.softwares:
            timestamp = self.strip_date(sw['publiccode']['releaseDate'])
            self.add_timestamp_to_metrics(timestamp)
            if 'it' in sw['publiccode'] and 'riuso' in sw['publiccode']['it'] and 'codiceIPA' in sw['publiccode']['it']['riuso']:
                self.metrics[timestamp]['num_softwares_reuse'] += 1

    def num_softwares_reusing(self):
        self.logger.info('Getting num softwares reusing...')
        if self.softwares is None:
            self._get_softwares()

        for sw in self.softwares:
            timestamp = self.strip_date(sw['publiccode']['releaseDate'])
            self.add_timestamp_to_metrics(timestamp)
            if 'usedBy' in sw['publiccode'] and sw['publiccode']['usedBy']:
                self.metrics[timestamp]['num_softwares_reusing'] += 1

    def vitality(self):
        self.logger.info('Getting software vitality...')
        if self.softwares is None:
            self._get_softwares()

        vitality = {}
        for sw in self.softwares:
            timestamp = self.strip_date(sw['publiccode']['releaseDate'])
            if timestamp not in vitality:
                vitality[timestamp] = { 'num': 0, 'val': 0 }
    
            vitality[timestamp]['num'] += 1
            if sw['vitalityDataChart'] is None:
                vitality[timestamp]['val'] += 0
            else:
                vitality[timestamp]['val'] += mean(sw['vitalityDataChart'])

        for ts, vit in vitality.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]['vitality'] = vit['val'] / vit['num']

    def num_pas_reusing(self):
        self.logger.info('Getting num reusing pas...')
        if self.softwares is None:
            self._get_softwares()

        listpa = {} 
        pa_seen = []
        for sw in self.softwares:
            # FIXME: non è la data corretta, da prendere da repolist
            timestamp = self.strip_date(sw['publiccode']['releaseDate']) 
            if timestamp not in listpa:
                listpa[timestamp] = []

            if 'usedBy' in sw['publiccode']:
                for pa in sw['publiccode']['usedBy']:
                    if pa.lower() not in listpa[timestamp] and pa.lower() not in pa_seen:
                        listpa[timestamp].append(pa.lower())
                        pa_seen.append(pa.lower())

        for ts, lst_pas in listpa.items():
            self.add_timestamp_to_metrics(ts)
            self.metrics[ts]['num_pas_reusing'] = len(lst_pas)
