#!/usr/bin/env python3

import argparse
import io
import os
import requests
import pandas as pd
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from common import MongoAction

# CIE EMESSE PER REGIONE: sum (Totale CIE Emesse)
# POPOLAZIONE TOTALE: sum (Popolazione)
# POPOLAZIONE POTENZIALE RAGGIUNTA: sum (Popolazione) dove Stato Comune = "Installato"

INT_fill = 0
DATE_fill = "01/01/1900"

date_column = [
    "Installazione prevista dal",
    "Installazione prevista al",
    "Data Prima Installazione",
    "Data Ultima Installazione",
    "Data Prima Attivazione Smart Card Operatore",
    "Data Prima Emissione"
]

int_column = [
    "Minuti Impiegati per Emissione",
    "Totale CIE in Spedizione",
    "Totale CIE Emesse Ultimi 3 Mesi",
    "Totale CIE Emesse",
    "Smart Card Operatore Attivate",
    "Totale Cittadini Registrati in AgendaCIE",
    "Percentuale CIE Emesse Ultimi 3 Mesi"
]

str_column = {
    "Provincia": str,
    "Codice ISTAT": str,
}


class CIE:
    def save_to_mongo(self, args, collection, collection_temp, data, method):
        mongoAction = MongoAction(args.mongodb_user, args.mongodb_pass, args.mongodb_db, args.mongodb_host, args.mongodb_authdb)
        mongoAction.createClient()

        if method:
            data_json = [row.to_dict() for idx, row in data.iterrows()]
            mongoAction.insertManyCollection(collection_temp, data_json)
        else:
            data_json = data.to_dict()
            mongoAction.insertCollection(collection_temp, data_json)

        mongoAction.renameCollection(collection_temp, collection)
        mongoAction.closeClient()

    def download_stats(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
        r = requests.get(url, headers=headers, allow_redirects=True).content
        return r

    def main(self, args):
        if args.env == 'production':
            file = self.download_stats(args.stats_url)
            cie = pd.read_csv(io.StringIO(file.decode('utf-8')), sep="\t", converters=str_column)
        elif args.env == 'development':
            filename = "{}/progettocie.csv".format(args.data_dir if opts.data_dir else ".")
            cie = pd.read_csv(filename, sep="\t", converters=str_column)
        else:
            raise Exception('A running environment should be specified (production or development).')

        cie[date_column] = cie[date_column].fillna(value=DATE_fill)
        cie[int_column] = cie[int_column].fillna(value=INT_fill)

        for i in date_column:
            cie[i] = pd.to_datetime(cie[i], format="%d/%m/%Y")
            cie[i] = pd.to_datetime(cie[i], unit='ms')

        # Tot Popolazione per regione
        f_totale = ['Regione', 'Popolazione']
        totale = cie[f_totale]
        totale = totale.groupby([totale['Regione']]).sum()

        # Tot Raggiunti/installato per regione
        f_raggiunti = ['Regione', 'Popolazione', 'Stato Comune']
        installati = cie[f_raggiunti]
        installati = installati[installati["Stato Comune"] == 'Installato']
        installati = installati.rename(columns={'Popolazione': 'Raggiunta'})
        raggiunti = installati.groupby([installati['Regione']]).sum()

        # Tot CIE per regione
        f_cie = ['Regione', 'Totale CIE Emesse']
        cie_esistenti = cie[f_cie]
        cie_esistenti = cie_esistenti.rename(columns={'Totale CIE Emesse': 'CIE'})
        cie_esistenti = cie_esistenti.groupby([cie['Regione']]).sum()
        totale_raggiunti = pd.merge(totale, raggiunti, left_index=True, right_index=True)

        final = pd.merge(totale_raggiunti, cie_esistenti, left_index=True, right_index=True)
        final["%Raggiunta"] = (final["Raggiunta"]/final["Popolazione"]*100).round(2)
        final["%Non Raggiunta"] = (100 - final["%Raggiunta"]).round(2)
        final["%CIE"] = (final["CIE"]/final["Popolazione"]*100).round(2)
        final["%NoCIE"] = (100-final["%CIE"])
        final["%CIE Pop raggiunta"] = (final["CIE"]/final["Raggiunta"]*100).round(2)
        final["%CIE Pop non raggiunta"] = (100-final["%CIE Pop raggiunta"])
        final = final.reset_index()

        # aggregati a livello nazione
        final_nazione = ["Popolazione", "Raggiunta", "CIE"]
        nazione = final[final_nazione].sum()
        nazione["%Raggiunta"] = (nazione["Raggiunta"]/nazione["Popolazione"]*100).round(2)
        nazione["%NonRaggiunta"] = (100 - nazione["%Raggiunta"]).round(2)

        nazione["%CIE"] = (nazione["CIE"]/nazione["Popolazione"]*100).round(2)
        nazione["%NonCIE"] = (100-nazione["%CIE"])

        # MONGO
        # insert data CIE
        self.save_to_mongo(args, "cie_comuni", "cie_tmp", cie, True)
        # insert data REGIONE
        self.save_to_mongo(args, "cie_regioni", "cie_regione_tmp", final, True)
        # insert data NAZIONE (1 record)
        self.save_to_mongo(args, "cie_italia", "cie_italia_tmp", nazione, False)


def GetParseOptions():
    parser = argparse.ArgumentParser(description="Program to manage files from CIE")
    parser.add_argument('--env', action="store", dest="env", type=str, choices=[
                            'production', 'development'], default=None, help="environment")
    parser.add_argument('--data-dir', action="store", dest="data_dir", type=str,
                        default=None, help="Directory to e used for storing data")
    parser.add_argument('--stats-url', action="store",
                        dest="stats_url", type=str, help="Address of the CSV file with the stats")
    parser.add_argument('--mongodb-db', action="store",
                        dest="mongodb_db", type=str, default=None, help="Mongodb DB")
    parser.add_argument('--mongodb-host', action="store",
                        dest="mongodb_host", type=str, default=None, help="Mongodb host")
    parser.add_argument('--mongodb-user', action="store", dest="mongodb_user",
                            type=str, default=None, help="Mongodb username")
    parser.add_argument('--mongodb-pass', action="store", dest="mongodb_pass",
                        type=str, default=None, help="Mongodb password")
    parser.add_argument('--mongodb-authdb', action="store",
                        dest="mongodb_authdb", type=str, default='admin', help="Mongodb Auth DB")
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    opts = GetParseOptions()
    CIE().main(opts)
