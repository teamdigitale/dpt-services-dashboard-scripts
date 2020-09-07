#!/usr/bin/env python3

import csv
import json
import re
import time
from datetime import datetime, timezone
import requests

from .engine import Engine


def response_is(response, code, message):
    """Convert an ISO 8601 string with timezone in a datetime object.

    Args:
        s (str): The ISO 8601 string
    Returns
        The datetime object
    """

    if response.content:
        answer = json.loads(response.content)

    return (response.status_code == code
            and (answer
                 and 'message' in answer
                 and message in answer['message']))

def to_datetime(s):
    """Convert an ISO 8601 string with timezone in a datetime object.

    Args:
        s (str): The ISO 8601 string
    Returns
        The datetime object
    """
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")


class GitHub(Engine):
    """
    Fetches the statistics from GitHub's API for repos in the /italia organization.

    It needs a GitHub token with push access to the repos to get the full stats
    (https://github.com/settings/tokens).
    """

    repos = None
    commits = None

    def __init__(self, args):
        super(GitHub, self).__init__(args, 'github')
        self.metric_names = ['num_members', 'num_repos', 'num_forks', 'num_contribs', 'num_commits', 'num_pr']

        if args.incremental:
            csv_path = "{}/{}.csv".format(args.data_dir, self.name)
            with open(csv_path, "r") as f:
                rows = csv.reader(f)

                try:
                    next(rows)  # Skip the header
                    last_row = (next(reversed(list(rows))))

                    ts = last_row[0]
                except (StopIteration, IndexError):
                    self.logger.error('--incremental needs at least one timestamp in %s.', csv_path)
                    raise

            self.args.since = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S%z')

    def _multiple_api_calls(self, url, repo_names, reduce=True):
        ret = {}

        for repo_name in repo_names:
            result = self._api_call(url.format(repo_name), reduce, repo_name)
            if result is not None:
                ret[repo_name] = result

        return ret

    def _api_call(self, url, reduce=True, name=None):
        if name is not None:
            self.logger.debug('Calling API for repo {} ({})...'.format(name, url))
        else:
            self.logger.debug('Calling {}'.format(url))

        headers = {'Authorization': 'token {}'.format(self.get_property('token_github'))}

        ret = []
        link = "{}?per_page=1000".format(url)

        while link is not None:
            while True:
                r = requests.get(link, headers=headers)

                answer = None
                if r.content:
                    answer = json.loads(r.content)

                # If we get rate-limited, take the hint and sleep until the reset time GitHub
                # provides us in the headers.
                #
                # 429 is returned when the API register too many requests from the same client.
                if (r.status_code == 429
                        or response_is(r, 403, 'API rate limit exceeded for user')
                        or response_is(r, 403, 'You have triggered an abuse detection mechanism')):

                    now = datetime.now(tz=timezone.utc)
                    until = datetime.fromtimestamp(int(r.headers['X-RateLimit-Reset']), tz=timezone.utc)
                    if until < now:
                        until = now

                    self.logger.debug("Rate limit reached, waiting until %s", until)
                    time.sleep((until - now).total_seconds())
                    self.logger.debug("Resuming API calls.")
                else:
                    break

            # Ignore empty repositories
            if response_is(r, 409, 'Git Repository is empty'):
                return None

            if r.status_code not in [200, 422]:
                if answer and 'message' in answer:
                    raise Exception('An error occurred while calling GitHub ({}): {}'.format(r.status_code, answer['message']))

                raise Exception('An error occurred while calling GitHub ({}).'.format(r.status_code))

            ret.append(answer)

            link = r.headers.get('link', None)
            if link is not None and re.search(r'; rel="next"', link):
                link = re.sub(r'.*<(.*)>; rel="next".*', r'\1', link)
            else:
                link = None

        if reduce:
            ret = [val for sublist in ret for val in sublist]

        return ret

    def _all_repos(self):
        """Fetch all the repos in the organization from day one.

        Returns: A list of dicts representing the repos.
        """

        if self.repos is None:
            self.repos = self._api_call('https://api.github.com/users/italia/repos', True)

        return self.repos

    def _all_commits_since(self):
        """Fetch all the commits in the organization.

        Returns: A list of dicts representing the commits.
        """

        if self.commits is None:
            self.logger.info('Getting commits from repos...')

            repo_names = [r['name'] for r in self._all_repos()]

            url = 'https://api.github.com/repos/italia/{}/commits'
            if self.args.since is not None:
                url += '?since={}'.format(self.args.since.strftime('%Y-%m-%dT%H:%M:%SZ'))

            self.commits = self._multiple_api_calls(url, repo_names, True)

        return self.commits

    def num_members(self):
        """Fetch the count of all members in the GitHub organization.

        It needs a token of a member of @italia to list both public and concealed members.
        This doesn't respect --since.
        """

        self.logger.info('Getting members...')

        # Use /members and count the elements of the returned array.
        members = self._api_call('https://api.github.com/orgs/italia/members', True)

        timestamp = self.strip_date(datetime.now(tz=timezone.utc))
        self.add_timestamp_to_metrics(timestamp)

        self.metrics[timestamp]['num_members'] = len(members)

    def num_repos(self):
        """Fetch the repos and index them by creation date."""

        self.logger.info('Getting repos...')
        repos = self._all_repos()

        if self.args.since is not None:
            repos = [r for r in repos if to_datetime(r['created_at']) >= self.args.since]

        for r in repos:
            timestamp = self.strip_date(r['created_at'])
            self.add_timestamp_to_metrics(timestamp)

            self.metrics[timestamp]['num_repos'] += 1

    def num_forks(self):
        """Fetch the forks and index them by creation date."""

        self.logger.info('Getting forks...')

        repo_names = [r['name'] for r in self._all_repos()]
        res = self._multiple_api_calls('https://api.github.com/repos/italia/{}/forks', repo_names, True)

        for _repo, forks in res.items():
            if self.args.since is not None:
                forks = [f for f in forks if to_datetime(f['created_at']) >= self.args.since]

            for f in forks:
                timestamp = self.strip_date(f['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_forks'] += 1

    def num_contribs(self):
        """Fetch the contribs that made at least one commit on one of the projects
        and index them by creation date."""

        self.logger.info('Getting contribs...')

        for a in self._all_commits_since():
            for c in self.commits[a]:
                timestamp = self.strip_date(c['commit']['author']['date'])

                # XXX: GitHub sometimes returns commits older than 'since' for some reason.
                # Let's discard those.
                if self.args.since is not None and to_datetime(timestamp) <= self.args.since:
                    continue

                self.add_timestamp_to_metrics(timestamp)

                if self.metrics[timestamp]['num_contribs'] == 0:
                    self.metrics[timestamp]['num_contribs'] = []

                if c['commit']['author']['name'] not in self.metrics[timestamp]['num_contribs']:
                    self.metrics[timestamp]['num_contribs'].append(c['commit']['author']['name'])

        for t in self.metrics:
            if 'num_contribs' in self.metrics[t]:
                if isinstance(self.metrics[t]['num_contribs'], list):
                    self.metrics[t]['num_contribs'] = len(self.metrics[t]['num_contribs'])

    def num_commits(self):
        """Fetch the commits made to all the projects in the GitHub organization and index them
        by creation date."""

        self.logger.info('Getting commits...')
        for a in self._all_commits_since().keys():
            for c in self.commits[a]:
                timestamp = self.strip_date(c['commit']['author']['date'])

                # XXX: GitHub sometimes returns commits older than 'since' for some reason.
                # Let's discard those.
                if self.args.since is not None and to_datetime(timestamp) <= self.args.since:
                    continue

                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_commits'] += 1

    def num_pr(self):
        """Fetch the pull requests made on all the projects in the GitHub organization."""

        self.logger.info('Getting PRs from repos...')

        repo_names = [r['name'] for r in self._all_repos()]

        # Use /issues because /pulls doesn't provide a 'since' argument
        url = 'https://api.github.com/repos/italia/{}/issues?state=all'
        if self.args.since is not None:
            url += '?since={}'.format(self.args.since.strftime('%Y-%m-%dT%H:%M:%SZ'))

        res = self._multiple_api_calls(url, repo_names, True)

        for _repo, pulls in res.items():
            pulls = [p for p in pulls if 'pull_request' in p]

            if self.args.since is not None:
                # /issues also returns the PRs _updated_ after '--since', but we
                # don't want those.
                pulls = [
                    p for p in pulls
                    if datetime.strptime(p['created_at'], "%Y-%m-%dT%H:%M:%S%z") >= self.args.since
                ]

            for p in pulls:
                timestamp = self.strip_date(p['created_at'])
                self.add_timestamp_to_metrics(timestamp)

                self.metrics[timestamp]['num_pr'] += 1

    def compute_stats(self):
        today = datetime.now(tz=timezone.utc).date()

        super(GitHub, self).compute_stats()

        # Filter out bogus stats in the future, if any.
        self.metrics = {
            ts: v for ts, v in self.metrics.items()
            if to_datetime(ts).date() <= today
        }

        # Put 'num_members' in the second to last metric, cause we're going
        # to discard the last one (today's).
        iterator = reversed(sorted(self.metrics))
        last_ts = next(iterator)
        try:
            second_last_ts = next(iterator)
            self.metrics[second_last_ts]['num_members'] = self.metrics[last_ts]['num_members']
        except StopIteration:
            pass

        # Remove today's data as it's not complete yet.
        del self.metrics[last_ts]

        return self.metrics
