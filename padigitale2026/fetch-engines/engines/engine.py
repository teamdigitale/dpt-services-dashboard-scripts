#!/usr/bin/env python3

from datetime import datetime

import os
import logging
import logging.config

class Engine(object):
    name = None
    logger = None
    args = None
    keyname = 'timestamp'

    num_threads = 1
    metrics = {}
    metric_names = []

    def __init__(self, args, engine_name):
        self.args = args
        self.name = engine_name

        self.num_threads = int(self.get_property('num_threads'))
        self.metrics = {}

        logging_conf = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../logging.conf')
        logging.config.fileConfig(fname=logging_conf, disable_existing_loggers=False)
        self.logger = logging.getLogger(engine_name)

    def get_property(self, property_name):
        if getattr(self.args, property_name, None):
            return getattr(self.args, property_name)

        # hack to keep backslah not doubled from encodind in env vars
        return bytes(os.getenv(property_name.upper()), 'latin1').decode('unicode_escape')

    def strip_date(self, in_timestamp):
        """
        Function that converts a datetime to the string of the datetime at the
        midnight of the day passed.
        """
        if isinstance(in_timestamp, str):
            if len(in_timestamp) <= 10:
                timestamp = datetime.strptime(in_timestamp, '%Y-%m-%d')
            else:
                try:
                    timestamp = datetime.strptime(in_timestamp, '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    timestamp = datetime.strptime(in_timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        else:
            timestamp = in_timestamp

        timestamp = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

        return timestamp

    def add_timestamp_to_metrics(self, timestamp):
        """
        Function that adds a timestamp to the metrics of this engine
        """
        if timestamp not in self.metrics:
            self.metrics[timestamp] = {}

            for metric in self.metric_names:
                self.metrics[timestamp][metric] = 0

    def compute_stats(self):
        for metric in self.metric_names:
            method_to_call = getattr(self, metric)
            method_to_call()

        return self.metrics
