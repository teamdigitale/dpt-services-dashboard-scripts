import json
import requests
from requests.auth import HTTPBasicAuth
import numpy as np
import re
from datetime import datetime
from .engine import Engine

class Newsletter(Engine):
    """
    Class that computes the statistics from users subscribed to newsletter:
    It retrieve metrics using a API key on Mailgun platform.

    Example of results:
    # python main.py -t newsletter
        timestamp,total_subscriber,group_by_pa_employee,group_by_pa_executive,group_by_pa_it_executive,group_by_pa_other,group_by_representative_pa,group_by_representative_supplier,group_by_representative_other
        2021-11-15T00:00:00Z,85,30,10,11,8,59,14,12
    """
    base_url = "https://api.eu.mailgun.net/v3/lists/newsletter@padigitale2026.gov.it/members/pages?limit=100&subscribed=yes"
    uuid_regex = r".\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b$"
    # website start date 2021-11-15
    website_start_date = '2021-11-15'
    result = None

    def __init__(self, args):
      super(Newsletter, self).__init__(args, 'newsletter')
      #each metric must have a corresponding method
      self.metric_names = ['total_subscriber', 'group_by_pa_employee',
        'group_by_pa_executive', 'group_by_pa_it_executive', 'group_by_pa_other',
        'group_by_representative_pa', 'group_by_representative_supplier', 'group_by_representative_other'
        ]


    def flattenjson(self, b, delim):
      val = {}
      for i in b.keys():
        if isinstance(b[i], dict):
          get = self.flattenjson(b[i], delim)
          for j in get.keys():
            val[i + delim + j] = get[j]
        else:
          val[i] = b[i]

      return val

    def unique(self, list1):
      unique_list_set = []
      unique_list = []

      # traverse for all elements
      for x in list1:
        # check if exists in unique_list or not
        if x['address'] not in unique_list_set:
          unique_list_set.append(x['address'])
          unique_list.append(x)

      return unique_list

    def cleanUUIDAndMessage(self, item):
      o = re.compile(self.uuid_regex).split(item['address'])
      item['uuid'] = item['address'].split(f'{o[0]}.')[1]
      item['address'] = o[0]
      if 'message' in item['vars']:
        item['vars']['message'] = item['vars']['message'].replace("\n", "")
      return item

    def makeRequest(self, url, items):
      API_KEY = self.get_property('token_mailgun')
      response = requests.get(f"{url}",
                  auth = HTTPBasicAuth('api', API_KEY))

      if response.status_code != 200:
        self.logger.error(f'error fetching data: {response.content}')
        return []

      content = json.loads(response.text)
      responseItems = content.get("items")
      nextPage = content["paging"]["next"]

      items = np.concatenate((items, responseItems))

      if nextPage and len(responseItems) > 0:
        self.logger.debug(f'next page present, here url: {nextPage}')
        return self.makeRequest(nextPage, items)

      return items

    def total_subscriber(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting total subscriber...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)
        self.metrics[timestamp]['total_subscriber'] +=1

    def group_by_pa_employee(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by PA employee...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['enteSelect']
        if enteSelect == 'dipendente-administration':
          self.metrics[timestamp]['group_by_pa_employee'] +=1

    def group_by_pa_it_executive(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by PA IT executive...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['enteSelect']
        if enteSelect == 'dirigente-it-administration':
          self.metrics[timestamp]['group_by_pa_it_executive'] +=1

    def group_by_pa_executive(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by PA executive...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['enteSelect']
        if enteSelect == 'dirigente-administration':
          self.metrics[timestamp]['group_by_pa_executive'] +=1

    def group_by_pa_other(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by PA other...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['enteSelect']
        if enteSelect == 'other':
          self.metrics[timestamp]['group_by_pa_other'] +=1

    def group_by_representative_supplier(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by representative supplier...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['representative']
        if enteSelect == 'fornitore-it':
          self.metrics[timestamp]['group_by_representative_supplier'] +=1

    def group_by_representative_pa(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by representative PA...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['representative']
        if enteSelect == 'public-administration':
          self.metrics[timestamp]['group_by_representative_pa'] +=1

    def group_by_representative_other(self):
      if self.result is None:
        self.retrieve_setup()

      self.logger.info('Getting by representative other...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)

        enteSelect = val['vars']['representative']
        if enteSelect == 'other':
          self.metrics[timestamp]['group_by_representative_other'] +=1

    def normalize_timestamp(self, vars):
      # at the beginning records did not have timestamp data
      if 'timestamp' in vars:
        return datetime.strptime(vars['timestamp'], '%Y-%m-%dT%H:%M:%S.%f%z').replace(hour=0, minute=0, second=0, microsecond=0)
      else:
        return datetime.strptime(self.website_start_date, '%Y-%m-%d')

    # retrieve data
    def all_metrics(self):
      items = self.makeRequest(self.base_url, [])
      self.logger.info(f'found {len(items)} items')

      # clean from UUID and get only unique
      return self.unique(list(map(self.cleanUUIDAndMessage, items)))

    # get data, setup timing, init counters
    def retrieve_setup(self):
      if self.result is None:
        self.result = self.all_metrics()

      self.logger.info('setting things up...')
      for val in self.result:
        cur_date = self.normalize_timestamp(val['vars'])
        timestamp = self.strip_date(cur_date)
        self.add_timestamp_to_metrics(timestamp)

        # init counters
        self.metrics[timestamp]['total_subscriber'] = 0
        if 'group_by_pa_employee' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_pa_employee'] = 0
        if 'group_by_pa_it_executive' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_pa_it_executive'] = 0
        if 'group_by_pa_executive' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_pa_executive'] = 0
        if 'group_by_pa_other' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_pa_other'] = 0
        if 'group_by_representative_supplier' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_representative_supplier'] = 0
        if 'group_by_representative_pa' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_representative_pa'] = 0
        if 'group_by_representative_other' not in self.metrics[timestamp]:
          self.metrics[timestamp]['group_by_representative_other'] = 0
