#!/usr/bin/env python

from datetime import datetime, timedelta
import time

from apiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
from google.auth import exceptions

from .engine import Engine

class GAnalytics(Engine):
    """
    Class that computes the statistics from Google Analytics sites: ....
    It retrieve metrics using a Google Service Account which not reqire OAuth2
    continous permission.
    Account needs to be created here:
    https://console.developers.google.com/apis/dashboard
    First, create a project, then a key under Credentials, 
    select Create Credentials -> Service Account Key
    when created, copy the email address generated for that key and add it to Google
    Analytics property users, here: https://analytics.google.com/analytics/web/#/a96140462w141653962p146203168/admin/suiteusermanagement/account

    Metrics list:
    https://ga-dev-tools.appspot.com/dimensions-metrics-explorer/


    Example of results:
    # python main.py -t ganalytics
        timestamp,unique_visits,new_users,sessions,page_views,ext_visits
        2019-09-30T00:00:00Z,518,394,583,1780,5.41
    """

    user_views = None
    auth = None
    countries = None

    def __init__(self, args):
        super(GAnalytics, self).__init__(args, 'ganalytics')
        #each metric must have a corresponding method
        self.metric_names = ['unique_visits', 'new_users', 'sessions', 'page_views', 'ext_visits', 'local_visits']

    def _auth(self):
        self.logger.info('Authenticating to Google using service account')
        # Authenticate and construct service.
        scope = 'https://www.googleapis.com/auth/analytics.readonly'

        # Generate auth JSON
        service_account_info = {
            "type": "service_account",
            "project_id": self.get_property('GOOGLE_PROJECT_ID'),
            "private_key_id": self.get_property('GOOGLE_PRIVATE_ID'),
            "private_key": self.get_property('GOOGLE_PRIVATE_KEY'),
            "client_email": self.get_property('GOOGLE_CLIENT_EMAIL'),
            "client_id": self.get_property('GOOGLE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": self.get_property('GOOGLE_CLIENT_X509_CERT_URL')
        }

        # Authenticate and construct service.
        service, profile_id = self._get_service(
                api_name='analytics',
                api_version='v3',
                scopes=[scope],
                service_account_info=service_account_info)
                
        return service, profile_id

    def get_first_profile_id(self, service):
        """Traverses Management API to return the first profile id.

        This first queries the Accounts collection to get the first account ID.
        This ID is used to query the Webproperties collection to retrieve the first
        webproperty ID. And both account and webproperty IDs are used to query the
        Profile collection to get the first profile id.

        Args:
            service: The service object built by the Google API Python client library.

        Returns:
            A string with the first profile ID. None if a user does not have any
            accounts, webproperties, or profiles.
        """

        self.logger.info('Getting google profile_id')
        accounts = service.management().accounts().list().execute()

        if accounts.get('items'):
            firstAccountId = accounts.get('items')[0].get('id')

            webPropertyID = self.get_property('GOOGLE_WPID')
            
            profiles = service.management().profiles().list(
                accountId=firstAccountId,
                webPropertyId=webPropertyID).execute()

            if profiles.get('items'):
                return profiles.get('items')[0].get('id')

        return None

    def _get_service(self, api_name, api_version, scopes, service_account_info):
        """
        Get a service that communicates to a Google API.

        Args:
            api_name: The name of the api to connect to.
            api_version: The api version to connect to.
            scopes: A list auth scopes to authorize for the application.
            key_file_location: The path to a valid service account JSON key file.

        Returns:
            A service that is connected to the specified API.
        """

        self.logger.info('Getting google service')
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        credentials.with_scopes(scopes)

        # Build the service object.
        service = build(api_name, api_version, credentials=credentials)

        # Try to make a request to the API. Print the results or handle errors.
        try:
            first_profile_id = self.get_first_profile_id(service)
            if not first_profile_id:
                self.logger.error('Could not find a valid profile for this user.')
                raise Exception('Could not find a valid profile for this user.')

        except TypeError as error:
            # Handle errors in constructing a query.
            self.logger.error(('There was an error in constructing your query : %s' % error))
            raise Exception('There was an error in constructing your query: {}'
                .format(error))

        except HttpError as error:
            # Handle API errors.
            self.logger.error(('Arg, there was an API error : %s : %s' %
                (error.resp.status, error._get_reason())))
            raise Exception('An error occurred while calling Google Analytics ({}): {}'
                .format(error.resp.status, error._get_reason()))

        except exceptions.RefreshError:
            # Handle Auth errors.
            self.logger.error('The credentials have been revoked or expired, please re-run '
                'the application to re-authorize')
            raise Exception('The credentials have been revoked or expired, please re-run '
                'the application to re-authorize')

        return service, first_profile_id

    def _api_call(self, metrics=[], dimensions=None, history=True):
        if (self.auth is None):
            self.logger.info('Not authenticated, authenticating...')
            service, profile_id = self._auth()
            self.auth = {
                service: service,
                profile_id: profile_id
            }
        else:
            self.logger.info('Already authenticated, skip auth')
            service, profile_id = self.auth

        # To get just one day you just need to specify
        # same day for start and end as well
        cur_date = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        first_date = cur_date
        if history:
            first_date = datetime.strptime('2017-01-01',"%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)

        ritorno = {}

        while cur_date >= first_date:
            cur_date = cur_date - timedelta(days=1)

            while True:
                try:
                    calldata = service.data().ga().get(
                        ids = 'ga:' + profile_id,
                        start_date = cur_date.strftime("%Y-%m-%d"), # '2019-08-01',
                        end_date = cur_date.strftime("%Y-%m-%d"), # '2019-08-31',
                        metrics = ','.join(metrics),
                        dimensions = dimensions,
                        start_index ='1',
                        max_results ='200').execute()

                    timestamp = self.strip_date(cur_date)
                    ritorno[timestamp] = calldata
                    break
                except HttpError:
                    self.logger.debug("Rate limit reached, waiting 60 seconds.")
                    time.sleep(60)
                    self.logger.debug("Restarting API calls.")

        return ritorno

    def _get_user_views(self):
        metrics = ['ga:users','ga:newUsers','ga:sessions','ga:pageviews']
        results = self._api_call(metrics=metrics)
        ritorno = {}

        for cur_date, value in results.items():
            ritorno[cur_date] = {}
            if value.get('rows', []):
                for row in value.get('rows'):
                    i = 0
                    for metric in metrics:
                        ritorno[cur_date][metric] = row[i]
                        i += 1

        return ritorno

    def unique_visits(self):
        self.logger.info('Getting num visits...')
        if self.user_views is None:
            self.user_views = self._get_user_views()

        for cur_date, value in self.user_views.items():
            timestamp = self.strip_date(cur_date)
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]['unique_visits'] = value['ga:users'] if 'ga:users' in value else 0

    def new_users(self):
        self.logger.info('Getting new users...')
        if self.user_views is None:
            self.user_views = self._get_user_views()

        for cur_date, value in self.user_views.items():
            timestamp = self.strip_date(cur_date)
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]['new_users'] = value['ga:newUsers'] if 'ga:newUsers' in value else 0

    def sessions(self):
        self.logger.info('Getting sessions...')
        if self.user_views is None:
            self.user_views = self._get_user_views()

        for cur_date, value in self.user_views.items():
            timestamp = self.strip_date(cur_date)
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]['sessions'] = value['ga:sessions'] if 'ga:sessions' in value else 0

    def page_views(self):
        self.logger.info('Getting page_views...')
        if self.user_views is None:
            self.user_views = self._get_user_views()

        for cur_date, value in self.user_views.items():
            timestamp = self.strip_date(cur_date)
            self.add_timestamp_to_metrics(timestamp)
            self.metrics[timestamp]['page_views'] = value['ga:pageviews'] if 'ga:pageviews' in value else 0

    def ext_visits(self):
        if self.countries is None:
            metrics = ['ga:users']
            dimensions = 'ga:country'
            self.countries = self._api_call(metrics=metrics, dimensions=dimensions, history=False)

        for cur_date, value in self.countries.items():
            total = 0
            notItaly = 0
            if value.get('rows', []):
                for row in value.get('rows'):
                    if len(row) == 2:
                        total += int(row[1])
                        if row[0]!= 'Italy':
                            notItaly += int(row[1])

                try:
                    timestamp = self.strip_date(cur_date)
                    self.add_timestamp_to_metrics(timestamp)
                    self.metrics[timestamp]['ext_visits'] = round((notItaly/total)*100,2)
                except ZeroDivisionError:
                    self.logger.error('Total views are 0, not possible to divide by 0')

    def local_visits(self):
        if self.countries is None:
            metrics = ['ga:users']
            dimensions = 'ga:country'
            self.countries = self._api_call(metrics=metrics, dimensions=dimensions, history=False)

        for cur_date, value in self.countries.items():
            total = 0
            italy = 0
            if value.get('rows', []):
                for row in value.get('rows'):
                    if len(row) == 2:
                        total += int(row[1])
                        if row[0] == 'Italy':
                            italy += int(row[1])

                try:
                    timestamp = self.strip_date(cur_date)
                    self.add_timestamp_to_metrics(timestamp)
                    self.metrics[timestamp]['local_visits'] = round((italy/total)*100,2)
                except ZeroDivisionError:
                    self.logger.error('Total views are 0, not possible to divide by 0')
