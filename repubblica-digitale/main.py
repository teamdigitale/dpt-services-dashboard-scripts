import httplib2

import argparse
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common import MongoAction

class RepubblicaDigitale:
    args = None

    def __init__(self, args):
        self.args = args

    def get_property(self, property_name):
        if getattr(self.args, property_name, None):
            return getattr(self.args, property_name)

    def save_to_mongo(self, args, collection, collection_temp, data, method):
        mongoAction = MongoAction(
            self.get_property('mongodb_user'),
            self.get_property('mongodb_pass'),
            self.get_property('mongodb_db'),
            self.get_property('mongodb_host'),
            self.get_property('mongodb_authdb'))

        mongoAction.createClient()

        if method:
            data_json = [row.to_dict() for idx, row in data.iterrows()]
            mongoAction.insertManyCollection(collection_temp, data_json)
        else:
            data_json = data.to_dict()
            mongoAction.insertCollection(collection_temp, data_json)

        mongoAction.renameCollection(collection_temp, collection)

        mongoAction.closeClient()

    def main(self):
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        spreadsheet_id = '1BV95DWqrytq1kSyP2EdFkJ0PSuGM5gdx0jhuS144tQI'
        range_name = 'Grafici!A1:C100'

        service_account_info = {
            "type": "service_account",
            "project_id": self.get_property('google_project_id'),
            "private_key_id": self.get_property('google_private_id'),
            "private_key": self.get_property('google_private_key'),
            "client_email": self.get_property('google_client_email'),
            "client_id": self.get_property('google_client_id'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": self.get_property('google_client_x509_cert_url')
        }

        # print(service_account_info)

        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        credentials.with_scopes(scopes)

        service = build('sheets', 'v4', credentials=credentials)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                    range=range_name).execute()
        values = result.get('values', [])

        repubblica_digitale_overall = []

        for row in values:
            if len(values) > 0:
                repubblica_digitale_overall.append({'categoria': row[0], 'tipologia': row[1], 'quantita': int(row[2])})

        self.save_to_mongo(args, "repubblica_digitale_overall", "repubblica_digitale_overall_tmp", pd.DataFrame(repubblica_digitale_overall), True)

def GetParseOptions():
    parser = argparse.ArgumentParser(description="Data ingestion for Repubblica Digitale")
    # Mongo
    parser.add_argument('--mongodb-db', action="store", dest="mongodb_db", type=str, default=None, help="Mongodb DB")
    parser.add_argument('--mongodb-host', action="store", dest="mongodb_host", type=str, default=None, help="Mongodb host")
    parser.add_argument('--mongodb-user', action="store", dest="mongodb_user", type=str, default=None, help="Mongodb username")
    parser.add_argument('--mongodb-pass', action="store", dest="mongodb_pass", type=str, default=None, help="Mongodb password")
    parser.add_argument('--mongodb-authdb', action="store", dest="mongodb_authdb", type=str, default='admin', help="Mongodb Auth DB")
    # Google Service Account
    parser.add_argument('--google_project_id', action="store", dest="google_project_id", type=str, help="Google Analytics Project ID")
    parser.add_argument('--google_private_id', action="store", dest="google_private_id", type=str, help="Google Analytics Private ID")
    parser.add_argument('--google_private_key', action="store", dest="google_private_key", type=str, help="Google Analytics Private Key")
    parser.add_argument('--google_client_email', action="store", dest="google_client_email", type=str, help="Google Analytics Client Email")
    parser.add_argument('--google_client_id', action="store", dest="google_client_id", type=str, help="Google Analytics Client ID")
    parser.add_argument('--google_client_x509_cert_url', action="store", dest="google_client_x509_cert_url", type=str, help="Google Analytics Client X509 Cert Url")
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = GetParseOptions()
    RepubblicaDigitale(args).main()
