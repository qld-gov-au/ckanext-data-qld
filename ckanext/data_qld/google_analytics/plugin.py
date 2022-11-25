# encoding: utf-8

from six.moves import queue as Queue
import json
import logging
from os import path
import requests
import threading
from six.moves.urllib.parse import urlencode

import ckan.plugins as p
from ckantoolkit import check_ckan_version, config


log = logging.getLogger('ckanext.googleanalytics')


class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ga_collection_url = config.get('ckan.data_qld_googleanalytics.collection_url',
                                            'https://www.google-analytics.com/collect')

    def run(self):
        # User-Agent must be present, GA might ignore a custom UA.
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        }
        while True:
            # Get host from the queue.
            data_dict = self.queue.get()
            log.debug("Sending API event to Google Analytics: " + data_dict['ea'])

            # Send analytics data.
            try:
                data = urlencode(data_dict)
                requests.post(self.ga_collection_url, data=data, headers=headers, timeout=5)
                self.queue.task_done()
            except requests.exceptions.RequestException:
                # If error occurred while posting - dont try again or attempt to fix  - just discard from the queue.
                self.queue.task_done()


class GoogleAnalyticsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)
    if check_ckan_version('2.8'):
        p.implements(p.IBlueprint)
        # workaround for https://github.com/ckan/ckan/issues/6678
        import ckan.views.api as core_api
    else:
        p.implements(p.IRoutes, inherit=True)

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
        GoogleAnalyticsPlugin.google_analytics_id = config.get('ckan.data_qld_googleanalytics.id')

        # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()

    # IRoutes

    def before_map(self, map):
        '''Add new routes that this extension's controllers handle.
        '''
        from routes.mapper import SubMapper
        # /api ver 3 or none
        with SubMapper(map, controller='ckanext.data_qld.google_analytics.controller:GoogleAnalyticsApiController',
                       path_prefix='/api{ver:/3|}', ver='/3') as m:
            m.connect('/action/{api_action}', action='action', conditions={'method': ['GET', 'POST']})

        return map

    # IBlueprint

    def get_blueprint(self):
        from . import blueprints
        return [blueprints.blueprint]
