#!/usr/bin/env python3

import json
import re
import concurrent.futures
import time
import datetime
import requests

from .engine import Engine

class GitHub(Engine):
    """
    Class that computes the statistics from GitHub repos of /italia organization.
    The class, to work, needs to have the key from a user with push access to the repos to execute.
    (the key can be created from this link: https://github.com/settings/tokens).
    All the statistics will be computed form the GitHub APIs.

    Example of results:
    # python main.py -t github
    Membri dell'organizzazione: 127.
    Numero di repo: 250.
    Numero di fork: 1,220.
    Numero di contributors distinti: 1,904.
    Numero di commit: 704,826.
    Numero di pull request: 5,610.
    Numero di clone: 945.
    """

    repos = None
    commits = None

    def __init__(self, args):
        super(GitHub, self).__init__(args, 'github')
        self.metric_names = ['num_members', 'num_repos', 'num_forks', 'num_contribs', 'num_commits', 'num_pr', 'num_clones']

    def _multiple_api_calls(self, url, iterlist, reduce=True):
        ritorno = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {executor.submit(self._api_call, url.format(p), reduce, p): p for p in iterlist}
            for future in concurrent.futures.as_completed(futures):
                name = futures[future]
                try:
                    ritorno[name] = future.result()
                except Exception as e:
                    self.logger.error('%s generated an exception: %s', name, e)
            
        return ritorno
                    
    def _api_call(self, url, reduce=True, name=None):
        if name is not None:
            self.logger.debug('Calling API for repo {}...'.format(name))

        headers = {'Authorization': 'token {}'.format(self.get_property('token_github'))}

        ritorno = []
        link = "{}?per_page=1000".format(url)
        
        while link is not None:
            while True:
                r = requests.get(link, headers=headers)

                answer = None
                if r.content:
                    answer = json.loads(r.content)

                # 429 is returned when the API register too many requests from the same client.
                # In this case wait some time and then retry the call.
                # Check also of the call returned an error message specifying you've triggered an abuse.
                if r.status_code == 429 or (answer and 'message' in answer and 'You have triggered an abuse detection mechanism' in answer['message']):
                    self.logger.debug("Rate limit reached, waiting 5 second.")
                    time.sleep(5)
                    self.logger.debug("Restarting API calls.")
                else:
                    break
            
            if r.status_code not in [200, 422, 409]:
                if answer and 'message' in answer:
                    raise Exception('An error occurred while calling GitHub ({}): {}'.format(r.status_code, answer['message']))
                
                raise Exception('An error occurred while calling GitHub ({}).'.format(r.status_code))

            if 'message' in answer:
                raise Exception('The call returned following message: {}'.format(answer['message']))

            ritorno.append(answer)

            link = r.headers.get('link', None)
            if link is not None and re.search(r'; rel="next"', link):
                link = re.sub(r'.*<(.*)>; rel="next".*', r'\1', link)
            else:
                link = None
        
        if reduce:
            ritorno = [val for sublist in ritorno for val in sublist]

        return ritorno

    def num_members(self):
        """
        Computable from https://api.github.com/orgs/italia/members by counting the elements of the returned array.
        Numeric indicator of the counting of all the members of the GitHub organization.
        """

        self.logger.info('Getting members...')
        members = self._api_call('https://api.github.com/orgs/italia/members', True)

        timestamp = self.strip_date(datetime.datetime.now())
        self.add_timestamp_to_metrics(timestamp)

        self.metrics[timestamp]['num_members'] = len(members)

    def num_repos(self):
        """
        Computable from https://api.github.com/users/italia/repos by counting the elements of the returned array.
        Numeric indicator of the counting of all the repos of the GitHub organization.
        """

        self.logger.info('Getting repos...')
        self.repos = self._api_call('https://api.github.com/users/italia/repos', True)

        for r in self.repos:
            timestamp = self.strip_date(r['created_at'])
            self.add_timestamp_to_metrics(timestamp)

            self.metrics[timestamp]['num_repos'] += 1

    def num_forks(self):
        """
        Computable from https://api.github.com/users/italia/repos by counting all the `forks_count` for all the repos.
        Numeric indicator of the forks for all the project of the GitHub organization.
        """

        if self.repos is None:
            self.num_repos()

        repo_names = [r['name'] for r in self.repos]
        forks = self._multiple_api_calls('https://api.github.com/repos/italia/{}/forks', repo_names, True)

        for r in forks:
            for f in forks[r]:
                timestamp = self.strip_date(f['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_forks'] += 1

    def num_contribs(self):
        """
        Computable from https://api.github.com/repos/italia/{REPONAME}/commits by summing all the commits
        for every different author on evenry repo obtained from the previous call.
        Numeric indicator of the number of contributors that made at least one commit on one of the
        projects of the GitHub organization.
        """

        self.logger.info('Getting commits from repos...')
        if self.commits is None:
            self.num_commits()
        
        for a in self.commits:
            for c in self.commits[a]:
                timestamp = self.strip_date(c['commit']['author']['date'])

                if self.metrics[timestamp]['num_contribs'] == 0:
                    self.metrics[timestamp]['num_contribs'] = []

                if c['commit']['author']['name'] not in self.metrics[timestamp]['num_contribs']:
                    self.metrics[timestamp]['num_contribs'].append(c['commit']['author']['name'])

        for t in self.metrics:
            if 'num_contribs' in self.metrics[t]:
                if isinstance(self.metrics[t]['num_contribs'], list):
                    self.metrics[t]['num_contribs'] = len(self.metrics[t]['num_contribs'])

    def num_commits(self):
        """
        Computable from https://api.github.com/repos/italia/{REPONAME}/commits by summing all the counting of the commits
        on all the repos obtained by the previous call.
        Numeric indicator of the number of commits made on all the projects of the GitHub organization.
        """

        self.logger.info('Getting commits from repos...')
        if self.repos is None:
            self.num_repos()

        repo_names = [r['name'] for r in self.repos]
        self.commits = self._multiple_api_calls('https://api.github.com/repos/italia/{}/commits', repo_names, True)

        for a in self.commits.keys():
            for c in self.commits[a]:
                timestamp = self.strip_date(c['commit']['author']['date'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_commits'] += 1

    def num_pr(self):
        """
        Computable from https://api.github.com/repos/italia/{REPONAME}/pulls by summing all the counting
        of the elements returned for every repo obtained from the previous call.
        Numeric indicator of the number of pull requests made on all the projects in the GitHub organization.
        """

        self.logger.info('Getting pulls from repos...')
        if self.repos is None:
            self.num_repos()

        repo_names = [r['name'] for r in self.repos]
        pulls = self._multiple_api_calls('https://api.github.com/repos/italia/{}/pulls', repo_names, True)

        for p in pulls:
            for r in pulls[p]:
                timestamp = self.strip_date(r['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_pr'] += 1

    def num_clones(self):
        """
        Computable from https://api.github.com/repos/italia/{REPONAME}/commits/traffic/clones by counting
        all the clones in the response to the call for every repo obtained from the previous call.
        Numeric indicator of all the git clones made on projects in the GitHub organization.
        """
        
        self.logger.info('Getting clones from repos...')
        if self.repos is None:
            self.num_repos()

        repo_names = [r['name'] for r in self.repos]
        clones = self._multiple_api_calls('https://api.github.com/repos/italia/{}/traffic/clones', repo_names, False)

        for a in clones:
            for c in clones[a][0]['clones']:
                timestamp = self.strip_date(c['timestamp'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_clones'] += c['count']
