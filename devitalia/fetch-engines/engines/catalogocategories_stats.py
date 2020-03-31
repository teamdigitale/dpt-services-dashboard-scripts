#!/usr/bin/env python3

import requests
import yaml
from .engine import Engine

class CatalogoCategories(Engine):
    """
    Class that computes the statistics from the reuse catalog from Developers Italia.
    
    Example of results:
    # python main.py -t catalogocategories
        slug,software_categories
        OPSILab-Idra-015316_1,data-visualization
        OPSILab-Idra-015316_2,data-collection
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

    softwares = None
    administrations = None

    def __init__(self, args):
        super(CatalogoCategories, self).__init__(args, 'catalogocategories')
        self.keyname = 'slug'
        #each metric must have a corresponding method
        self.metric_names = ['software_categories']

    def _get_softwares(self):
        sws = requests.get(self.SOFTWARES_URL).content
        sws = yaml.safe_load(sws)
        self.softwares = sws

    def software_categories(self):
        self.logger.info('Getting softwares\' categories...')
        if self.softwares is None:
            self._get_softwares()

        for sw in self.softwares:
            if 'categories' in sw['publiccode']:
                categories = sw['publiccode']['categories']
            else:
                categories = []

            i = 1
            for c in categories:
                swid = "%s_%d" % (sw['slug'], i)
                self.add_timestamp_to_metrics(swid)
                self.metrics[swid]['software_categories'] = c
                i += 1
