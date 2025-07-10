# encoding: utf-8

import queue as Queue
import json
import logging
from os import path
import requests
import threading

import ckan.plugins as p
from ckantoolkit import config


log = logging.getLogger('ckanext.googleanalytics')


class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ga_collection_url = config.get('ckanext.data_qld_googleanalytics.ga4_collection_url',
                                            'https://www.google-analytics.com/mp/collect')

    def run(self):
        # User-Agent must be present, GA might ignore a custom UA.
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        }
        while True:
            # Get host from the queue.
            data_dict = self.queue.get()
            log.debug("Sending API event to Google Analytics: " + data_dict['ea'])

            # Send analytics data.
            try:
                requests.post(self.ga_collection_url, json=data_dict, headers=headers, timeout=5)
                self.queue.task_done()
            except requests.exceptions.RequestException:
                # If error occurred while posting - dont try again or attempt to fix  - just discard from the queue.
                self.queue.task_done()


class GoogleAnalyticsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IBlueprint)
    # workaround for https://github.com/ckan/ckan/issues/6678
    import ckan.views.api as core_api

    analytics_queue = Queue.Queue()
    capture_api_actions = {}
    google_analytics_id = None

    def configure(self, config):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        # Load capture_api_actions from JSON file
        here = path.abspath(path.dirname(__file__))
        with open(path.join(here, 'capture_api_actions.json')) as json_file:
            GoogleAnalyticsPlugin.capture_api_actions = json.load(json_file)

        # Get google_analytics_id from config file
        GoogleAnalyticsPlugin.google_analytics_id = config.get('ckanext.data_qld_googleanalytics.Ga4Id')

        # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()

    # IBlueprint

    def get_blueprint(self):
        from . import blueprints
        return [blueprints.blueprint]
