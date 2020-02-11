#!/usr/bin/env python

from pymongo import MongoClient

class MongoAction:

    host = None
    db = None
    username = None
    password = None
    client = None
    authdb = None

    def __init__(self, username, password, db, host, authdb):
        self.username = username
        self.password = password
        self.db = db
        self.host = host
        self.authdb = authdb

    def createClient(self):
        self.client = MongoClient(host=self.host,
            username=self.username,
            password=self.password,
            authSource=self.authdb)

    def closeClient(self):
        self.client.close()

    def saveObject(self, collectionName, obj):
        self.client[self.db][collectionName].insert_one(obj)

    def insertCollection(self, collection, obj):
        self.client[self.db][collection].insert_one(obj)

    def insertManyCollection(self, collection, obj):
        self.client[self.db][collection].insert_many(obj)

    def dropAndInsertCollection(self, collection, obj):
        self.client[self.db][collection].drop()
        self.insertCollection(collection, obj)

    def dropAndRenameCollection(self, newCollection, oldCollection):
        self.client[self.db][newCollection].drop()
        self.client[self.db][oldCollection].rename(newCollection)

    def renameCollection(self, oldCollection, newCollection):
        self.client[self.db][oldCollection].rename(newCollection, dropTarget=True)
