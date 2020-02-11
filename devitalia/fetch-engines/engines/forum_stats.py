#!/usr/bin/env python

import json
import concurrent.futures
import datetime
import time
import requests

from .engine import Engine

class Forum(Engine):
    """
    Class that computes the statistics from the Forum of developers /italia.
    The calls to the Discourse API require authentication. For this reason it is necessary to create
    an API key from the administration panel.

    Once you obtained the API key, this can be used for authentication passing to the HTTP calls two
    parameters in the header:
        - Api-Key: whith the value just created
        - Api-Username: with the username of the users used to access the forum

    Example of results:
    # python main.py -t forum
    Number of registered users to the developers /italia forum: 100.
    Number of users of the developers /italia forum active today: 45.
    Number of pages visited for the developers /italia forum for today: 1,937.
    Number of messages posted in the developers /italia forum: 18,014.
    Number of likes on posts on the developers /italia forum: 19,805.
    Number of reads on the posts on the developers /italia forum: 737,370.
    """

    users = None
    posts = None

    def __init__(self, args):
        super(Forum, self).__init__(args, 'forum')
        self.metric_names = ['num_registered_users', 'num_active_users', 'num_pageviewes', 'num_topics', 'num_posts', 'num_likes', 'num_reads']

    def _api_call(self, url, reduce=True, paginate=False):
        headers = {
            'Api-Key': '{}'.format(self.get_property('forum_api_key')),
            'Api-Username': 'dashboard-scripts'
        }

        ritorno = []
        link = "{}".format(url)
        curpage = 0
    
        while link is not None:
            if paginate:
                curpage += 1
                link = "{}?page={}".format(link, curpage)

            while True:
                r = requests.get(link, headers=headers)
                # 429 is returned when the API register too many requests from the same client.
                # In this case wait some time and then retry the call.
                if r.status_code == 429:
                    self.logger.debug("Rate limit reached, waiting 40 seconds.")
                    time.sleep(40)
                    self.logger.debug("Restarting API calls.")
                else:
                    break

            answer = None

            if r.content:
                answer = json.loads(r.content)
            
            if r.status_code not in [200, 422, 409]:
                if answer and 'errors' in answer:
                    raise Exception('An error occurred while calling Slack ({}): {}'.format(r.status_code, answer['errors']))
                
                raise Exception('An error occurred while calling Slack ({}).'.format(r.status_code))

            if 'errors' in answer:
                raise Exception('The call returned following message: {}'.format(answer['errors']))

            ritorno.append(answer)

            if paginate:
                link = "{}".format(url) if len(answer) > 0 else None
            else:
                link = None

        if reduce:
            ritorno = [val for sublist in ritorno for val in sublist]

        return ritorno

    def _multiple_api_calls(self, url, iterlist, reduce=True):
        ritorno = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {executor.submit(self._api_call, url % p, reduce=reduce): p for p in iterlist}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    ritorno[name] = future.result()
                except Exception as e:
                    self.logger.error('%s generated an exception: %s', name, e)
            
        return ritorno

    def _get_all_posts(self):
        cur_posts = self._api_call('https://forum.italia.it/posts.json', reduce=False)
        self.posts = cur_posts
        
        last_id = max([p['id'] for p in cur_posts[0]['latest_posts']])
        query_ids = []

        while last_id > 0:
            last_id -= 50
            if last_id > 0:
                query_ids.append(last_id)

        url = 'https://forum.italia.it/posts.json?before=%d'
        results = self._multiple_api_calls(url, query_ids, False)
        for r in results.values():
            self.posts.extend(r)
    
    def num_registered_users(self):
        """
        Computable from https://forum.italia.it/admin/users/list/active.json by counting all
        the elements of the returned array.
        Numeric indicator of the number of registered user to the developers /italia forum.
        """

        self.logger.info('Getting registered users...')
        self.users = self._api_call('https://forum.italia.it/admin/users/list/active.json', paginate=True, reduce=True)
        
        for u in self.users:
            timestamp = self.strip_date(u['created_at'])
            self.add_timestamp_to_metrics(timestamp)

            self.metrics[timestamp]['num_registered_users'] += 1

    def num_active_users(self):
        """
        Computable from https://forum.italia.it/admin/users/list/active.json by counting all
        the elements of the returned array with last_seen_age in the current day.
        Numeric indicator of the number of users of the developers /italia forum active today.
        """

        self.logger.info('Getting active users...')
        if self.users is None:
            self.num_registered_users()

        for u in self.users:
            timestamp = u['last_seen_at'] if 'last_seen_at' in u else None

            if timestamp:
                timestamp = self.strip_date(u['last_seen_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_active_users'] += 1

    def num_pageviewes(self):
        """
        Computable from https://forum.italia.it/admin/reports/page_view_total_reqs.json by passing parameters
        start_date and end_date and then by summing the values of data->y of the corresponding record for the
        current day.
        Numeric indicator of the number of pages visited for the developers /italia forum for today.
        """

        self.logger.info('Getting page views...')
        cur_startdate = datetime.datetime.now() + datetime.timedelta(days=1)
        dates = []

        while cur_startdate >= datetime.datetime(2017, 1, 1):
            cur_enddate = cur_startdate - datetime.timedelta(days=1)
            cur_startdate = cur_enddate - datetime.timedelta(days=30)
            dates.append((cur_startdate.strftime('%Y-%m-%d'), cur_enddate.strftime('%Y-%m-%d')))

        url = 'https://forum.italia.it/admin/reports/page_view_total_reqs.json?start_date=%s&end_date=%s'
        pages = self._multiple_api_calls(url, dates, False)

        for c in pages:
            for p in pages[c][0]['report']['data']:
                timestamp = p['x'] + "T00:00:00Z"
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_pageviewes'] += p['y']

    def num_topics(self):
        """
        Computable from https://forum.italia.it/admin/reports/topics.json by counting elements of the returned
        array when called with parameters start_date and end_date and summing the value of data->y corrisponding
        to the current date.
        Numeric indicator of the number of topics posted on the developers /italia forum.
        """

        self.logger.info('Getting topics...')
        cur_startdate = datetime.datetime.now() + datetime.timedelta(days=1)
        dates = []

        while cur_startdate >= datetime.datetime(2017, 1, 1):
            cur_enddate = cur_startdate - datetime.timedelta(days=1)
            cur_startdate = cur_enddate - datetime.timedelta(days=30)
            dates.append((cur_startdate.strftime('%Y-%m-%d'), cur_enddate.strftime('%Y-%m-%d')))

        url = 'https://forum.italia.it/admin/reports/topics.json?start_date=%s&end_date=%s'
        pages = self._multiple_api_calls(url, dates, False)

        for c in pages:
            for p in pages[c][0]['report']['data']:
                timestamp = p['x'] + "T00:00:00Z"
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_topics'] += p['y']

    def num_posts(self):
        """
        Computable from https://forum.italia.it/posts.json by counting the elements of the retuned array in
        the field latest_posts. For the pagination it is necessaro to use the parameter before by passing
        the id of the oldest message minus 1 until you reach message with id 1.
        Numeric indicator of the number of messages posted in the developers /italia forum.
        """

        self.logger.info('Getting posts...')
        if self.posts is None:
            self._get_all_posts()

        for c in self.posts:
            for p in c['latest_posts']:
                timestamp = self.strip_date(p['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_posts'] += 1

    def num_likes(self):
        """
        Computable from https://forum.italia.it/posts.json by summing the values of the field
        actions_summary with id equals to 2 of all the elements of the retuned array in the
        field latest_posts.
        For the pagination it is necessaro to use the parameter before by passing the id of the
        oldest message minus 1 until you reach message with id 1.
        Numeric indicator of the likes on the posts of the developers /italia forum.
        """

        self.logger.info('Getting likes...')
        if self.posts is None:
            self._get_all_posts()

        for c in self.posts:
            for p in c['latest_posts']:
                timestamp = self.strip_date(p['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                for a in p['actions_summary']:
                    if a['id'] == 2:
                        self.metrics[timestamp]['num_likes'] += a['count'] if 'count' in a else 1

    def num_reads(self):
        """
        Computable from https://forum.italia.it/posts.json by summing all the values of the field
        reads for all the elements of the returned array in the field latest_posts.
        For the pagination it is necessaro to use the parameter before by passing the id of the
        oldest message minus 1 until you reach message with id 1.
        Numeric indicator of the reads of all the posts of the developers /italia forum.
        """

        self.logger.info('Getting reads...')
        if self.posts is None:
            self._get_all_posts()

        for c in self.posts:
            for p in c['latest_posts']:
                timestamp = self.strip_date(p['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_reads'] += p['reads']
