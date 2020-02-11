#!/usr/bin/env python

import json
import concurrent.futures
import datetime
import re
import time
from urllib.parse import urlencode
import requests

from .engine import Engine

class Slack(Engine):
    """
    Class that computes the statistics from Slack's workspace of /italia organization.
    The class, to work, needs to have or a legacy token or an installed app on the workspace.
    (more info here: https://api.slack.com/web#authentication).
    All the statistics will be computed form the Slack APIs.

    Example of results:
    # python main.py -t slack
    Number of registered users to the developers /italia workspace: 2,825.
    Number of active users to the developers /italia workspace: 25.
    Number of channels in the developers /italia workspace: 83.
    Number of messages sent today on all channels of the developers /italia workspace: 8.
    """

    num_threads = 1

    registered_users = None
    channels = None
    messages = None

    def __init__(self, args):
        super(Slack, self).__init__(args, 'slack')
        self.metric_names = ['num_registered_users', 'num_channels', 'num_messages', 'num_replies']

    def _api_call(self, url, field, reduce=True, name=None):
        if name is not None:
            self.logger.debug('Calling API for channel %s...', name)

        params = {'token': self.get_property('token_slack')}
        link = url

        ritorno = []        
        while link is not None:
            while True:
                if '?' in url:
                    link = '{}&{}'.format(url, urlencode(params))
                else:
                    link = '{}?{}'.format(url, urlencode(params))

                r = requests.get(link)
                
                answer = None

                if r.content:
                    answer = json.loads(r.content)

                # 429 is returned when the API register too many requests from the same client.
                # In this case wait some time and then retry the call.
                # Check also of the call returned an error message specifying you've triggered an abuse.
                if r.status_code == 429 or (answer and 'message' in answer and 'You have triggered an abuse detection mechanism' in answer['message']):
                    self.logger.debug("Rate limit reached, waiting 30 second.")
                    time.sleep(30)
                    self.logger.debug("Restarting API calls.")
                else:
                    break

            if r.status_code not in [200, 422, 409]:
                if answer and 'error' in answer:
                    raise Exception('An error occurred while calling Slack ({}): {}'.format(r.status_code, answer['error']))

                raise Exception('An error occurred while calling Slack ({}).'.format(r.status_code))

            if 'error' in answer:
                raise Exception('The call returned following message: {}'.format(answer['error']))

            ritorno.append(answer[field])

            if 'has_more' in answer and answer['has_more']:
                cursor = answer['response_metadata']['next_cursor']
                params['cursor'] = cursor
            else:
                link = None

        if reduce:
            ritorno = [val for sublist in ritorno for val in sublist]

        return ritorno

    def _multiple_api_calls(self, url, iterlist, field, reduce=True):
        ritorno = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {executor.submit(self._api_call, url.format(p), field, reduce, p): p for p in iterlist}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    ritorno[name] = future.result()
                except Exception as e:
                    self.logger.error('%s generated an exception: %s', name, e)

        return ritorno

    def num_registered_users(self):
        """
        Computable from https://developersitalia.slack.com/api/users.list by counting the elements of the returned array.
        Numeric indicator of the counting of the registered users to the workspace developers /italia.
        """

        self.logger.info('Getting registered users...')
        call_response = self._api_call('https://developersitalia.slack.com/api/users.list', 'members', False)
        self.registered_users = call_response[0]

        timestamp = self.strip_date(datetime.datetime.now())
        self.add_timestamp_to_metrics(timestamp)

        self.metrics[timestamp]['num_registered_users'] = len(self.registered_users)

    def num_channels(self):
        """
        Computable from https://developersitalia.slack.com/api/channels.list by counting the number of
        elements in the returned array.
        Numeric indicator of the number of channels on the workspace developers /italia.
        """
        
        self.logger.info('Getting channels users...')
        call_response = self._api_call('https://developersitalia.slack.com/api/channels.list?exclude_archived=true', 'channels', False)
        self.channels = call_response[0]

        for c in self.channels:
            timestamp = self.strip_date(datetime.datetime.fromtimestamp(c['created']))
            self.add_timestamp_to_metrics(timestamp)

            self.metrics[timestamp]['num_channels'] += 1

        return len(self.channels)

    def num_messages(self):
        """
        Computable from https://developersitalia.slack.com/api/conversations.history by doing a call for every
        channel returned from the previous call and counting the elements returned in the message.
        The call returns by default a maximim number of 100 messages, to verify to have counted all of them
        it is neccessary to check the has_more parameter. It it is true another call needs to be done
        using the ts of the last message as the latest parameter for the new call.
        Numeric indicator of the number of messages sent on all channels on the workspace developers /italia.
        """

        self.logger.info('Getting messages...')
        if self.channels is None:
            self.num_channels()

        channel_ids = [c['id'] for c in self.channels]
        self.messages = self._multiple_api_calls('https://developersitalia.slack.com/api/conversations.history?channel={}', channel_ids, 'messages', True)

        for a in self.messages:
            for m in self.messages[a]:
                ts = re.sub('\.\d*', '', m['ts'])
                timestamp = self.strip_date(datetime.datetime.fromtimestamp(int(ts)))
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_messages'] += 1

    def num_replies(self):
        """
        Computable from https://developersitalia.slack.com/api/conversations.history by doing a call for every
        channel returned from the previous call and counting the elements returned in the message.
        The call returns by default a maximim number of 100 messages, to verify to have counted all of them
        it is neccessary to check the has_more parameter. It it is true another call needs to be done
        using the ts of the last message as the latest parameter for the new call.
        Numeric indicator of the number of message replies sent on all channels on the workspace developers /italia.
        """

        self.logger.info('Getting replies...')
        if self.messages is None:
            self.num_messages()

        for a in self.messages:
            for m in self.messages[a]:
                ts = re.sub('\.\d*', '', m['ts'])
                timestamp = self.strip_date(datetime.datetime.fromtimestamp(int(ts)))
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_replies'] += len(m['replies']) if 'replies' in m else 0
