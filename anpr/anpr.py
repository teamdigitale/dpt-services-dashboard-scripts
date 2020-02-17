#!/usr/bin/env python3

import csv
import datetime
import http.client
import json
import argparse
import urllib.parse
import urllib.request

from xml.etree import cElementTree as ET

_FORNITORE_SCONOSCIUTO = 'Fornitore non pervenuto'


class GeoLocator():

    def __init__(self, apikey, cache_file, dry_run=False, debug=False):
        self._dry_run = dry_run
        self._debug = debug
        self._apikey = apikey
        self._conn = http.client.HTTPSConnection('maps.googleapis.com')
        self._cache_file = cache_file
        self._cache = {}

    def _MaybeLoadCache(self):
        try:
            self._cache = json.load(open(self._cache_file))
        except Exception as e:
            print('Could not load maps cache: %s' % e)

    def _MaybeSaveCache(self):
        try:
            json.dump(self._cache, open(self._cache_file, 'w'), indent=2)
        except Exception as e:
            print('Could not save maps cache: %s' % e)

    @staticmethod
    def _GetComuneCacheKey(comune):
        return '%s_%s_%s' % (comune['nome'], comune['provincia'], comune['regione'])

    def _CacheLookup(self, comune):
        return self._cache.get(self._GetComuneCacheKey(comune), (None, None))

    def _CacheStore(self, comune, lat, lon):
        self._cache[self._GetComuneCacheKey(comune)] = (lat, lon)

    def _GMapsLookup(self, address):
        if self._dry_run:
            print('Would perform lookup for',
                  address, 'returning fake coords.')
            return 42.0, 42.0

        params = urllib.parse.urlencode({
            'key': self._apikey,
            'address': address,
        }, 'utf-8')
        self._conn.request('GET', '/maps/api/geocode/json?%s' % params)

        response = self._conn.getresponse()
        data = json.loads(response.read())
        location = data['results'][0]['geometry']['location']

        return location['lat'], location['lng']

    @staticmethod
    def _GenAddresses(comune):
        return [
            '%(nome)s %(provincia)s %(regione)s' % comune,
            '%(nome)s %(provincia)s' % comune,
            '%(nome)s Italy' % comune,
            '%(nome)s' % comune,
        ]

    def Lookup(self, comune):
        lat, lon = self._CacheLookup(comune)
        if lat and lon:
            return lat, lon

        for address in self._GenAddresses(comune):
            try:
                lat, lon = self._GMapsLookup(address)
            except Exception as e:
                if self._debug:
                    print('ERROR with address ',
                          address.encode('utf-8'), ': ', e)
            else:
                break

        if not lat or not lon:
            lat = 41.894802
            lon = 12.485338
            print('ERROR: Could not find coordinates for %s' % comune)
        #  raise Exception('ERROR: Could not find coordinates for %s' % comune)

        self._CacheStore(comune, lat, lon)
        return lat, lon

    def CreateGeoDocuments(self, comuni):
        self._MaybeLoadCache()
        docs = []
        for comune in comuni:
            doc = {
                'COMUNE': comune['nome'],
                'PROVINCIA': comune['provincia'],
                'REGIONE': comune['regione'],
            }
            if comune['lat'] and comune['lon']:
                doc['LAT'], doc['LON'] = comune['lat'], comune['lon']
            else:
                doc['LAT'], doc['LON'] = self.Lookup(comune)
            docs.append(doc)
        self._MaybeSaveCache()
        return docs


class Comune():

    def __init__(self, codice_istat, nome, provincia, regione):
        self._data = {}
        self._data['codice_istat'] = codice_istat
        self._data['nome'] = nome
        self._data['provincia'] = provincia
        self._data['regione'] = regione
        self._data['lat'] = None
        self._data['lon'] = None
        self._data['fornitore'] = _FORNITORE_SCONOSCIUTO
        self._data['in_subentro'] = False
        self._data['data_subentro'] = datetime.datetime.min
        self._data['abitanti_subentro'] = 0
        self._data['abitanti_subentro_aire'] = 0
        self._data['in_presubentro'] = False
        self._data['data_presubentro'] = datetime.datetime.min
        self._data['abitanti_presubentro'] = 0
        self._data['stima_prima_data_subentro'] = datetime.datetime.min
        self._data['stima_ultima_data_subentro'] = datetime.datetime.min
        self._data['stima_data_subentro_preferita'] = datetime.datetime.min
        self._data['stima_abitanti'] = 0

    @classmethod
    def FromData(cls, base_fields, data_item):
        return cls(
            data_item[base_fields['codice_istat']],
            data_item[base_fields['nome']],
            data_item[base_fields['provincia']],
            data_item[base_fields['regione']])

    def __str__(self):
        return '%s, %s, %s (codice istat: %s)' % (
            self._data['nome'], self._data['provincia'], self._data['regione'],
            self._data['codice_istat'])

    def Set(self, name, value):
        if name not in self._data:
            raise Exception('Key "%s" should be defined first' % name)
        self._data[name] = value

    def Get(self, name):
        return self._data[name]

    def GetInconsistencies(self):
        report = []

        if self._data['fornitore'] == _FORNITORE_SCONOSCIUTO:
            report.append('Comune senza fornitore: %s' % self)

        ultima_data_subentro = self._data['stima_ultima_data_subentro']
        if (not self._data['in_subentro']
            and ultima_data_subentro > datetime.datetime.min
                and PastDateConsideringStaleData(ultima_data_subentro)):
            report.append('Superata ultima data stimata per subentro (%s): %s' % (
                ultima_data_subentro.strftime('%Y/%m/%d'), self))

        data_subentro_preferita = self._data['stima_data_subentro_preferita']
        if (not self._data['in_subentro']
            and data_subentro_preferita > datetime.datetime.min
                and PastDateConsideringStaleData(data_subentro_preferita)):

            report.append('Superata data preferita stimata per subentro (%s): %s' % (
                data_subentro_preferita.strftime('%Y/%m/%d'), self))

        return report

    def AsDocument(self):
        return self._data


class Fornitore():

    def __init__(self, nome):
        self._data = {}
        self._data['nome'] = nome
        self._data['totale_comuni'] = 0
        self._data['comuni_subentrati'] = 0
        self._data['comuni_in_presubentro'] = 0
        self._data['totale_popolazione'] = 0
        self._data['popolazione_subentrata'] = 0
        self._data['popolazione_in_presubentro'] = 0

    def AddSubentrato(self, popolazione):
        self._data['comuni_subentrati'] += 1
        self._data['totale_comuni'] += 1
        self._data['popolazione_subentrata'] += popolazione
        self._data['totale_popolazione'] += popolazione

    def AddInPresubentro(self, popolazione):
        self._data['comuni_in_presubentro'] += 1
        self._data['totale_comuni'] += 1
        self._data['popolazione_in_presubentro'] += popolazione
        self._data['totale_popolazione'] += popolazione

    def AddInattivo(self, popolazione):
        self._data['totale_comuni'] += 1
        self._data['totale_popolazione'] += popolazione

    def AsDocument(self):
        doc = self._data.copy()

        totale_comuni = float(doc['totale_comuni'])
        comuni_subentrati = float(doc['comuni_subentrati'])
        comuni_in_presubentro = float(doc['comuni_in_presubentro'])
        comuni_inattivi = totale_comuni - \
            (comuni_subentrati + comuni_in_presubentro)
        doc['percentuale_comuni_inattivi'] = comuni_inattivi * 100 / totale_comuni
        doc['percentuale_comuni_in_presubentro'] = comuni_in_presubentro * \
            100 / totale_comuni
        doc['percentuale_comuni_subentrati'] = comuni_subentrati * \
            100 / totale_comuni

        totale_popolazione = float(doc['totale_popolazione'])
        popolazione_subentrata = float(doc['popolazione_subentrata'])
        popolazione_in_presubentro = float(doc['popolazione_in_presubentro'])
        popolazione_inattiva = totale_popolazione - (
            popolazione_subentrata + popolazione_in_presubentro)
        doc['percentuale_popolazione_inattiva'] = popolazione_inattiva * \
            100 / totale_popolazione
        doc['percentuale_popolazione_in_presubentro'] = popolazione_in_presubentro * \
            100 / totale_popolazione
        doc['percentuale_popolazione_subentrata'] = popolazione_subentrata * \
            100 / totale_popolazione

        return doc


class ProiezioneSubentro():

    def __init__(self, codice_istat, nome, provincia, regione, data_subentro,
                 abitanti_subentro):
        self._data = {}
        self._data['codice_istat'] = codice_istat
        self._data['nome'] = nome
        self._data['provincia'] = provincia
        self._data['regione'] = regione
        self._data['data_subentro'] = data_subentro
        self._data['abitanti_subentro'] = abitanti_subentro

    @classmethod
    def FromComune(cls, comune):
        # We need to build a graph with the current set of comuni subentrati, plus
        # the estimates for the future. If comune is already subentrato use that
        # data, otherwise use the estimates. If no estimate is available do not
        # build a datapoint at all.
        if (not comune.Get('in_subentro')
                and comune.Get('stima_ultima_data_subentro') == datetime.datetime.min):
            return None

        if comune.Get('in_subentro'):
            data = comune.Get('data_subentro')
            abitanti = comune.Get('abitanti_subentro')
        else:
            if comune.Get('stima_data_subentro_preferita') > datetime.datetime.min:
                data = comune.Get('stima_data_subentro_preferita')
            elif comune.Get('stima_ultima_data_subentro') > datetime.datetime.min:
                data = comune.Get('stima_ultima_data_subentro')

            if comune.Get('abitanti_presubentro') > 0:
                abitanti = comune.Get('abitanti_presubentro')
            else:
                abitanti = comune.Get('stima_abitanti')

        return cls(
            codice_istat=comune.Get('codice_istat'),
            nome=comune.Get('nome'),
            provincia=comune.Get('provincia'),
            regione=comune.Get('regione'),
            data_subentro=data,
            abitanti_subentro=abitanti,
        )

    def AsDocument(self):
        return self._data


class StatoComuni():

    def __init__(self):
        self._state = {}

    def AddFieldsFrom(self, data, base_fields, specific_fields):
        for data_item in data:
            codice_istat = data_item[base_fields['codice_istat']]
            comune = self._state.get(codice_istat)
            if not comune:
                comune = Comune.FromData(base_fields, data_item)
                self._state[codice_istat] = comune
            for name, field_data in specific_fields.iteritems():
                orig_key, func = field_data
                comune.Set(name, func(data_item[orig_key]))

    def OnlySubentroCollection(self):
        return [c.AsDocument() for c in self._state.values()
                if c.Get('in_subentro')]

    def OnlyPresubentroCollection(self):
        return [c.AsDocument() for c in self._state.values()
                if c.Get('in_presubentro') and c.Get('in_subentro')]

    def ReportInconsistencies(self):
        for comune in self._state.values():
            for inconsistency in comune.GetInconsistencies():
                print(inconsistency.encode('utf-8'))

    def BuildStatoFornitori(self):
        fornitori = {}
        for comune in self._state.values():
            fornitore = fornitori.setdefault(
                comune.Get('fornitore'), Fornitore(comune.Get('fornitore')))
            if comune.Get('in_subentro'):
                fornitore.AddSubentrato(comune.Get('abitanti_subentro'))
            elif comune.Get('in_presubentro'):
                fornitore.AddInPresubentro(comune.Get('abitanti_presubentro'))
            else:
                fornitore.AddInattivo(comune.Get('stima_abitanti'))

        return [f.AsDocument() for f in fornitori.values()]

    def BuildProiezioniSubentro(self):
        proiezioni = []

        for comune in self._state.values():
            proiezione = ProiezioneSubentro.FromComune(comune)
            if proiezione:
                proiezioni.append(proiezione)

        return [p.AsDocument() for p in proiezioni]

    def AsCollection(self):
        return [c.AsDocument() for c in self._state.values()]


def RenameFields(comuni, orig_field, new_field):
    for comune in comuni:
        if orig_field in comune:
            comune[new_field] = comune[orig_field]


def ConvertFields(comuni, fields, func):
    for comune in comuni:
        for field in fields:
            comune[field] = func(comune[field])


__month_ita_lookup_table = {
    'GEN':  1,
    'FEB':  2,
    'MAR':  3,
    'APR':  4,
    'MAG':  5,
    'GIU':  6,
    'LUG':  7,
    'AGO':  8,
    'SET':  9,
    'OTT': 10,
    'NOV': 11,
    'DIC': 12,
}


def ConvertTimestamp(timestring):
    try:
        return datetime.datetime.strptime(timestring, '%d/%m/%Y')
    except ValueError:
        day_str, month_ita, year_str = timestring.split('-')
        orig_date = datetime.datetime(int('20%s' % year_str),
                                      __month_ita_lookup_table[month_ita],
                                      int(day_str))
        return orig_date


def PastDateConsideringStaleData(dt):
    # SOGEI updates subentro data only once a week, on Monday. Consider a date in
    # the past only after data has been updated (that is, only after Tuesday of
    # the week after).
    start_week = dt - datetime.timedelta(days=dt.weekday())
    past_update = start_week + datetime.timedelta(days=8)
    return past_update < datetime.datetime.now()


def ParseCSV(filename):
    return [r for r in csv.DictReader(open(filename))]


def SaveCsvToDaf(dafkey, filePath):
    payload = open(filePath, 'rb').read()
    header = {
        'Content-Type': 'text/csv',
        'Authorization': 'Basic %s' % dafkey
    }
    request = urllib.request.Request(url='https://api.daf.teamdigitale.it/hdfs/proxy/uploads/d_ale/SOCI/demografia/anpr_con_aire/anpr.csv?op=CREATE',
                                     headers=header,
                                     data=payload,
                                     method='PUT')
    urllib.request.urlopen(request)


def ParseXML(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    rows = []
    for xml_row in root:
        row = {}
        for column in xml_row:
            text = ''
            if column.text:
                text = column.text.strip()
            name = column.attrib.get('NAME')
            if not name:
                name = column.tag
            row[name] = text
        rows.append(row)

    return rows


def PrintState(collections):
    def collection_serializer(obj):
        if isinstance(obj, (datetime.datetime)):
            return obj.isoformat()
        return obj

    for collection, data in collections.iteritems():
        print("===== BEGIN %s =====" % collection)
        print(json.dumps(data, indent=2, default=collection_serializer))
        print("=====  END %s  =====" % collection)


def SaveToMongo(collections):
    import pymongo

    client = pymongo.MongoClient()
    db = client.get_database('monitor_mdb')

    for collection, data in collections.iteritems():
        temp_collection = '_temp_%s' % collection
        for row in data:
            db[temp_collection].insert_one(row)
        # if temp_collection in db.collection_names():
        db[temp_collection].rename(collection, dropTarget=True)


def GetParseOptions():
    parser = argparse.ArgumentParser(description="Program to manage files from ANPR")
    parser.add_argument('--maps-apikey', action="store", dest="maps_apikey", type=str,
        default=None, help="Google Maps API Key")
    parser.add_argument('--daf-apikey', action="store", dest="daf_apikey", type=str,
        default=None, help="DAF API Key", required=True)
    parser.add_argument('--maps-cache', action="store", dest='maps_cache', type=str,
        default=None, help='Google Maps Lookups Cache')
    parser.add_argument('--comuni-subentrati', action="store", dest='comuni_subentrati', type=str,
        default=None, help='XML Comuni Subentrati')
    parser.add_argument('--comuni-presubentro', action="store", dest='comuni_presubentro', type=str,
        default=None, help='XML Comuni Presubentro')
    parser.add_argument('--anomalie', action="store", dest='anomalie', type=str,
        default=None, help='XML Anomalie Presubentro')
    parser.add_argument('--anomalie-ag-entrate', action="store", dest='anomalie_ag_entrate', type=str,
        default=None, help='XML Anomalie Presubentro Ag. Entrate')
    parser.add_argument('--piano-subentro', action="store", dest='piano_subentro', type=str,
        default=None, help='CSV Piano Subentro')
    parser.add_argument('--dry-run', action="store_true", dest='dry_run', help='Do not upload data to Mongo')
    parser.add_argument('--debug', action="store_true", dest='debug', help='Produce debugging output')
    args = parser.parse_args()

    return args


def main():
    opts = GetParseOptions()
    #piano_subentro = ParseCSV(opts.piano_subentro)
    SaveCsvToDaf(opts.daf_apikey, opts.piano_subentro)

    #comuni_subentrati = ParseXML(opts.comuni_subentrati)
    #comuni_presubentro = ParseXML(opts.comuni_presubentro)
    #anomalie = ParseXML(opts.anomalie)
    #anomalie_ag_entrate = ParseXML(opts.anomalie_ag_entrate)


'''
  stato_comuni = StatoComuni()

  stato_comuni.AddFieldsFrom(
      data=comuni_subentrati,
      base_fields={
        'codice_istat': 'CODICEISTAT',
        'nome': 'DENOMINAZIONE',
        'provincia': 'PROVINCIA',
        'regione': 'REGIONE',
      },
      specific_fields={
        'in_subentro': ('DATA_SUBENTRO', lambda x: True),
        'data_subentro': ('DATA_SUBENTRO', ConvertTimestamp),
        'abitanti_subentro': ('NUMERO_ABITANTI', int),
        'abitanti_subentro_aire': ('NUMERO_SOGGETTI_AIRE', int)
      },
  )

  stato_comuni.AddFieldsFrom(
      data=comuni_presubentro,
      base_fields={
        'codice_istat': 'CODICEISTAT',
        'nome': 'DENOMINAZIONE',
        'provincia': 'PROVINCIA',
        'regione': 'REGIONE',
      },
      specific_fields={
        'in_presubentro': ('DATASUBENTRO', lambda x: True),
        'data_presubentro': ('DATASUBENTRO', ConvertTimestamp),
        'abitanti_presubentro': ('NUMEROABITANTI', int),
      },
  )

  stato_comuni.AddFieldsFrom(
      data=piano_subentro,
      base_fields={
        'codice_istat': 'codice_istat',
        'nome': 'nome_comune',
        'provincia': 'provincia',
        'regione': 'regione',
      },
      specific_fields={
        'lat': ('lat', lambda x: None if not x else float(x)),
        'lon': ('lon', lambda x: None if not x else float(x)),
        'fornitore': ('fornitore', lambda x: x),
        'stima_prima_data_subentro': (
            'prima_data_subentro',
            lambda x: datetime.datetime.min if not x else datetime.datetime.strptime(x, '%d/%m/%Y')),
        'stima_ultima_data_subentro': (
            'ultima_data_subentro',
            lambda x: datetime.datetime.min if not x else datetime.datetime.strptime(x, '%d/%m/%Y')),
        'stima_data_subentro_preferita': (
            'data_subentro_preferita',
            lambda x: datetime.datetime.min if not x else datetime.datetime.strptime(x, '%d/%m/%Y')),
        'stima_abitanti': ('popolazione', int),
      },
  )

  geolocator = GeoLocator(opts.maps_apikey, opts.maps_cache, opts.dry_run, opts.debug)
  subentro_geo = geolocator.CreateGeoDocuments(stato_comuni.OnlySubentroCollection())
  presubentro_geo = geolocator.CreateGeoDocuments(stato_comuni.OnlyPresubentroCollection())

  RenameFields(anomalie, 'NUMEROANOMALIE', 'NUMNEROANOMALIE')
  
  ConvertFields(
      anomalie,
      ['NUMNEROANOMALIE', 'NUMEROABITANTIISTAT', 'NUMEROSCHEDESOGGETTOINVIATE'],
      lambda x: 0 if not x else int(x))
  ConvertFields(
      anomalie_ag_entrate,
      ['NUMEROANOMALIE', 'NUMEROABITANTIISTAT', 'NUMEROSCHEDESOGGETTOINVIATE'],
      lambda x: 0 if not x else int(x))

  stato_comuni.ReportInconsistencies()

  collections = {
    'anpr_stato_comuni': stato_comuni.AsCollection(),
    'anpr_stato_fornitori': stato_comuni.BuildStatoFornitori(),
    'anpr_proiezioni_subentro': stato_comuni.BuildProiezioniSubentro(),
    'anpr_geolocation_subentro': subentro_geo,
    'anpr_geolocation_presubentro': presubentro_geo,
    #'anpr_anomalie': anomalie,
    #'anpr_anomalie_agenzia_entrate': anomalie_ag_entrate,
  }

  if opts.dry_run:
    PrintState(collections)
  else:
    SaveToMongo(collections)
'''

if __name__ == '__main__':
    main()
