#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ast
import csv
import argparse
from datetime import datetime
from common import MongoAction


class PaDigitale:
    def guess_types(self, row):
        attempt_fns = [ast.literal_eval,
            int,
            float,
            lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")]

        for fieldname in row:
            for fn in attempt_fns:
                try:
                    row[fieldname] = fn(row[fieldname])
                    break
                except (ValueError, SyntaxError):
                    pass
        return row

    def main(self, args):
        for file in os.listdir(args.data_dir):
            if file.endswith(".csv"):
                print("Processing file {}...".format(file))
                engine = file.replace('.csv', '').lower()

                filename = os.path.join(args.data_dir, file)
                with open(filename, "r") as csvfile:
                    mongoAction = MongoAction(args.mongodb_user, args.mongodb_pass, args.mongodb_db, args.mongodb_host, args.mongodb_authdb)
                    mongoAction.createClient()

                    datareader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
                    for row in datareader:
                        row = self.guess_types(row)
                        mongoAction.saveObject('padigitale_{}_new'.format(engine), row)

                    mongoAction.renameCollection('padigitale_{}_new'.format(engine), 'padigitale_{}'.format(engine))
                    mongoAction.closeClient()

def GetParseOptions():
    parser = argparse.ArgumentParser(description="Program to manage files from Developers Italia")
    parser.add_argument('--data-dir', action="store", dest="data_dir", type=str,
                        default=None, help="Directory to e used for storing data")
    parser.add_argument('--mongodb-host', action="store", dest="mongodb_host",
                        type=str, default=None, help="Mongodb host")
    parser.add_argument('--mongodb-user', action="store", dest="mongodb_user",
                            type=str, default=None, help="Mongodb username")
    parser.add_argument('--mongodb-pass', action="store", dest="mongodb_pass",
                        type=str, default=None, help="Mongodb password")
    parser.add_argument('--mongodb-db', action="store",
                        dest="mongodb_db", type=str, default=None, help="Mongodb DB")
    parser.add_argument('--mongodb-authdb', action="store",
                        dest="mongodb_authdb", type=str, default='admin', help="Mongodb Auth DB")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    opts = GetParseOptions()
    PaDigitale().main(opts)
