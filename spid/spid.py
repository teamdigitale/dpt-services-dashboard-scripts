#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
import pandas
import argparse
from common import MongoAction


FASCIA_ETA_TRANS = dict([(1, "18-24"), (2, "24-34"), (3, "35-44"), (4, "45-54"),
                         (5, "55-64"), (6, "65-74"), (7, ">75"), (8, "Sconosciuta"), (9, "18-24")])
SESSO_TRANS = dict([(1, "Maschile"), (2, "Femminile"), (3, "Non dichiarato")])
MODALITA_RILASCIO_TRANS = dict(
    [(1, "Online cie"), (2, "Online webcam"), (3, "Offline")])


class Spid:
    params = None

    def manageSpid(self, filePath, tableName):
        data = pandas.read_csv(filePath, sep='\t')
        total = data['total'].sum()
        objs = data.transpose().to_dict().values()
        providers = []

        mongoAction = MongoAction(self.params.mongodb_user,
                                    self.params.mongodb_pass,
                                    self.params.mongodb_db,
                                    self.params.mongodb_host,
                                    self.params.mongodb_authdb)
        mongoAction.createClient()

        for obj in objs:
            week = obj['week']  # .astype(int)
            year = obj['year']  # .astype(int)
            atime = time.asctime(time.strptime(
                '{} {} 1'.format(year, week), '%Y %W %w'))
            datetime_object = datetime.strptime(
                str(atime), '%a %b %d %H:%M:%S %Y')
            obj['data'] = datetime_object
            keys = obj.keys()
            for key in keys:
                if key == 'TIM ID' or key == 'POSTE ID' or key == 'SIELTE ID' or key == 'INFOCERT ID' or key == 'ARUBA' or key == 'Register' or key == 'Namirial' or key == 'Intesa' or key == 'Lepida':
                    provider = {}
                    provider['provider'] = key
                    provider['week'] = week
                    provider['year'] = year
                    provider['count'] = obj[key]
                    provider['data'] = obj['data']
                    providers.append(provider)

        for prov in providers:
            mongoAction.insertCollection(tableName + '_tmp', prov)
        mongoAction.renameCollection(tableName + '_tmp', tableName)
        mongoAction.closeClient()
        
        if tableName == 'spid_overall_final':
            #tot_2017 = data.loc[(data['year'] == 2017) & (data['week'] <= 18), 'total'].sum()
            #tot_2018 = data.loc[(data['year'] == 2018) & (data['week'] <= 18), 'total'].sum()
            tot_2016 = data.loc[data['year'] == 2016, 'total'].sum()
            crescita = int(((float(total) - float(tot_2016)) / tot_2016) * 100)

            mongoAction = MongoAction(self.params.mongodb_user,
                                        self.params.mongodb_pass,
                                        self.params.mongodb_db,
                                        self.params.mongodb_host,
                                        self.params.mongodb_authdb)
            mongoAction.createClient()
            
            mongoAction.dropAndInsertCollection('spid_crescita', {'crescita': crescita})
            mongoAction.closeClient()

        return total

    def manageDetails(self, filePath):
        data = pandas.read_csv(filePath, sep='\t')
        objs = data.transpose().to_dict().values()

        mongoAction = MongoAction(self.params.mongodb_user,
                                    self.params.mongodb_pass,
                                    self.params.mongodb_db,
                                    self.params.mongodb_host,
                                    self.params.mongodb_authdb)
        mongoAction.createClient()
        
        for obj in objs:
            week_year = obj['NUM_SETTIMANA'].split('_')
            week = week_year[1]
            year = week_year[0]
            atime = time.asctime(time.strptime(
                '{} {} 1'.format(year, week), '%Y %W %w'))
            datetime_object = datetime.strptime(
                str(atime), '%a %b %d %H:%M:%S %Y')
            obj['data'] = datetime_object
            fascia_eta = FASCIA_ETA_TRANS[obj['FASCIA_ETA']]
            obj['FASCIA_ETA_DESC'] = fascia_eta
            sesso = SESSO_TRANS[obj['SESSO']]
            obj['SESSO_DESC'] = sesso
            mod_rilascio = MODALITA_RILASCIO_TRANS[obj['MODALITA_RILASCIO']]
            obj['MODALITA_RILASCIO_DESC'] = mod_rilascio
            mongoAction.insertCollection('spid_details_tmp', obj)

        mongoAction.renameCollection('spid_details_tmp', 'spid_details')
        mongoAction.closeClient()

    def normalizeModalita(self, filePath, total):
        data = pandas.read_csv(filePath, sep='\t')
        total_prev = data['ID_RILASCIATE'].sum()
        test = data.groupby(['MODALITA_RILASCIO'])['ID_RILASCIATE'].sum()

        mongoAction = MongoAction(self.params.mongodb_user,
                                    self.params.mongodb_pass,
                                    self.params.mongodb_db,
                                    self.params.mongodb_host,
                                    self.params.mongodb_authdb)
        mongoAction.createClient()

        total_diff = 0
        for n, index in enumerate(test.index):
            if n != len(test.index) - 1:
                mod_rilascio = MODALITA_RILASCIO_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                final = {'Modalita_rilascio': mod_rilascio, 'totale': diff}
                mongoAction.insertCollection('MODALITA_RILASCIO_tmp', final)
            else:
                mod_rilascio = MODALITA_RILASCIO_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                offset = 0
                if (total - total_diff) > 0:
                    offset = total - total_diff
                final = {'Modalita_rilascio': mod_rilascio, 'totale': diff + offset}
                mongoAction.insertCollection('MODALITA_RILASCIO_tmp', final)
                
        mongoAction.renameCollection('MODALITA_RILASCIO_tmp', 'MODALITA_RILASCIO')
        mongoAction.closeClient()

    def normalizeEta(self, filePath, total):
        data = pandas.read_csv(filePath, sep='\t')
        total_prev = data['ID_RILASCIATE'].sum()
        test = data.groupby(['FASCIA_ETA'])['ID_RILASCIATE'].sum()

        mongoAction = MongoAction(self.params.mongodb_user,
                                    self.params.mongodb_pass,
                                    self.params.mongodb_db,
                                    self.params.mongodb_host,
                                    self.params.mongodb_authdb)
        mongoAction.createClient()
        
        total_diff = 0
        for n, index in enumerate(test.index):
            if n != len(test.index) - 1:
                fascia_eta = FASCIA_ETA_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                final = {'Fascia_eta': fascia_eta, 'totale': diff}
                mongoAction.insertCollection('FASCIA_ETA_tmp', final)
            else:
                fascia_eta = FASCIA_ETA_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                offset = 0
                if (total - total_diff) > 0:
                    offset = total - total_diff
                final = {'Fascia_eta': fascia_eta, 'totale': diff + offset}
                mongoAction.insertCollection('FASCIA_ETA_tmp', final)

        mongoAction.renameCollection('FASCIA_ETA_tmp', 'FASCIA_ETA')
        mongoAction.closeClient()

    def normalizeSesso(self, filePath, total):
        data = pandas.read_csv(filePath, sep='\t')
        total_prev = data['ID_RILASCIATE'].sum()
        test = data.groupby(['SESSO'])['ID_RILASCIATE'].sum()

        mongoAction = MongoAction(self.params.mongodb_user,
                                    self.params.mongodb_pass,
                                    self.params.mongodb_db,
                                    self.params.mongodb_host,
                                    self.params.mongodb_authdb)
        mongoAction.createClient()
        
        total_diff = 0
        for n, index in enumerate(test.index):
            if n != len(test.index) - 1:
                sesso = SESSO_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                final = {'sesso': sesso, 'totale': diff}
                mongoAction.insertCollection('SESSO_tmp', final)
            else:
                sesso = SESSO_TRANS[index]
                perc = test[index]
                diff = (perc * total) / total_prev
                total_diff = total_diff + diff
                offset = 0
                if (total - total_diff) > 0:
                    offset = total - total_diff
                final = {'sesso': sesso, 'totale': diff + offset}
                mongoAction.insertCollection('SESSO_tmp', final)
        
        mongoAction.renameCollection('SESSO_tmp', 'SESSO')
        mongoAction.closeClient()

    def getParseOptions(self):
        parser = argparse.ArgumentParser(description="SPID processor")
        parser.add_argument('--data-path-dest', action="store", dest="data_path_dest", type=str,
                            default=None, help="Directory to e used for storing data")
        parser.add_argument('--mongodb-user', action="store", dest="mongodb_user",
                            type=str, default=None, help="Mongodb username")
        parser.add_argument('--mongodb-pass', action="store", dest="mongodb_pass",
                            type=str, default=None, help="Mongodb password")
        parser.add_argument('--mongodb-db', action="store",
                            dest="mongodb_db", type=str, default=None, help="Mongodb DB")
        parser.add_argument('--mongodb-host', action="store",
                            dest="mongodb_host", type=str, default=None, help="Mongodb Host")
        parser.add_argument('--mongodb-authdb', action="store",
                            dest="mongodb_authdb", type=str, default='admin', help="Mongodb Auth DB")
        args = parser.parse_args()

        return args

    def main(self):
        self.params = self.getParseOptions()
        data_path_dest = self.params.data_path_dest

        total = self.manageSpid(f"{data_path_dest}/overall.csv", 'spid_overall_final')
        self.manageSpid(f"{data_path_dest}/eighteen.csv", 'spid_eighteen')
        self.manageDetails(f"{data_path_dest}/details.csv")
        self.normalizeEta(f"{data_path_dest}/details.csv", total)
        self.normalizeModalita(f"{data_path_dest}/details.csv", total)
        self.normalizeSesso(f"{data_path_dest}/details.csv", total)


if __name__ == '__main__':
    Spid().main()
