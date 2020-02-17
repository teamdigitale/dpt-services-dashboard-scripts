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
        OPSILab-Idra-015316_1,government
        OPSILab-Idra-015316_2,local-authorities
        OPSILab-Idra-015316_3,research
    """

    '''
    Relevant files:
    - https://developers.italia.it/crawler/softwares.yml
    - https://developers.italia.it/crawler/amministrazioni.yml
    - https://developers.italia.it/crawler/software_categories.yml
    - https://developers.italia.it/crawler/software-open-source.yml
    - https://developers.italia.it/crawler/software-riuso.yml
    - https://developers.italia.it/crawler/software_scopes.yml
    - https://developers.italia.it/crawler/software_tags.yml
    '''

    SOFTWARES_URL = 'https://developers.italia.it/crawler/softwares.yml'

    softwares = None
    administrations = None

    def __init__(self, args):
        super(CatalogoAudiences, self).__init__(args, 'catalogoaudiences')
        self.keyname = 'slug'
        #each metric must have a corresponding method
        self.metric_names = ['software_audiences']

    def _get_softwares(self):
        sws = requests.get(self.SOFTWARES_URL).content
        sws = yaml.safe_load(sws)
        self.softwares = sws

    def software_audiences(self):
        self.logger.info('Getting softwares\' audiences...')
        if self.softwares is None:
            self._get_softwares()

        for sw in self.softwares:
            if 'intendedAudience' in sw['publiccode'] and 'scope' in sw['publiccode']['intendedAudience']:
                audience = sw['publiccode']['intendedAudience']['scope']
            else:
                audience = []

            i = 1
            for a in audience:
                swid = "%s_%d" % (sw['slug'], i)
                self.add_timestamp_to_metrics(swid)
                self.metrics[swid]['software_audiences'] = a
                i += 1
