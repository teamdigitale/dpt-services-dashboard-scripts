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

    regioni = [
        'Abruzzo', 'Basilicata', 'Calabria', 'Campania',
        'Emilia Romagna', 'Friuli Venezia Giulia', 'Lazio',
        'Liguria', 'Lombardia', 'Marche', 'Molise', 'Piemonte',
        'Puglia', 'Sardegna', 'Sicilia', 'Toscana',
        'Trentino Alto Adige', 'Umbria', 'Valle D\'Aosta', 'Veneto'
    ]
    softwares = None
    administrations = None

    def __init__(self, args):
        super(CatalogoRegioni, self).__init__(args, 'catalogoregioni')
        self.keyname = 'regione'
        #each metric must have a corresponding method
        self.metric_names = ['num_pas', 'num_softwares']

        for regione in self.regioni:
            self.metrics[regione] = {}
            for metric in self.metric_names:
                self.metrics[regione][metric] = 0

    def _get_softwares(self):
        sws = requests.get(self.SOFTWARES_URL).content
        sws = yaml.safe_load(sws)
        self.softwares = sws

    def _get_administrations(self):
        pas = requests.get(self.INDICEPA_URL).content
        pas = pas.decode("utf-8")
        pas = pas.split('\n')
        self.administrations = []
        
        titles = pas[0].split('\t')
        for p in pas[1:]:
            arr = { }
            values = p.split('\t')
            for i in range(0, len(values)):
                arr[titles[i]] = values[i]
            self.administrations.append(arr)
            
    def num_pas(self):
        self.logger.info('Getting num PAs...')
        if self.softwares is None:
            self._get_softwares()
        if self.administrations is None:
            self._get_administrations()

        listpa = {}
        for sw in self.softwares:
            if 'it' in sw['publiccode'] and 'riuso' in sw['publiccode']['it'] and 'codiceIPA' in sw['publiccode']['it']['riuso']:
                newpa = sw['publiccode']['it']['riuso']['codiceIPA'].lower()
                regione = None
                for a in self.administrations:
                    if a['cod_amm'].lower() == newpa:
                        regione = a['Regione']

                if not regione: continue
                if regione not in listpa: listpa[regione] = []
                if newpa not in listpa[regione]: listpa[regione].append(newpa)

        for reg, lst_pas in listpa.items():
            self.metrics[reg]['num_pas'] = len(lst_pas)

    def num_softwares(self):
        self.logger.info('Getting num softwares...')
        if self.softwares is None:
            self._get_softwares()
        if self.administrations is None:
            self._get_administrations()

        for sw in self.softwares:
            if 'it' in sw['publiccode'] and 'riuso' in sw['publiccode']['it'] and 'codiceIPA' in sw['publiccode']['it']['riuso']:
                newpa = sw['publiccode']['it']['riuso']['codiceIPA'].lower()
                regione = None
                for a in self.administrations:
                    if a['cod_amm'].lower() == newpa:
                        regione = a['Regione']

                if not regione: continue
                self.metrics[regione]['num_softwares'] += 1
