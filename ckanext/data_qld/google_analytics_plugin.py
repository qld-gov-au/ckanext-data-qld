import logging
import urllib
import requests
import ckan.plugins as p
from routes.mapper import SubMapper
from pylons import config

import threading
import Queue

log = logging.getLogger('ckanext.googleanalytics')


class AnalyticsPostThread(threading.Thread):
    """Threaded Url POST"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ga_collection_url = config.get('ckan.data_qld_googleanalytics.collection_url', 'https://www.google-analytics.com/collect')

    def run(self):
        #User-Agent must be present, GA might ignore a custom UA
        headers = {
            'Content-Type':'application/x-www-form-urlencoded',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'
        }
        while True:
            # grabs host from queue
            data_dict = self.queue.get()
            log.debug("Sending API event to Google Analytics: " + data_dict['ea'])
            # send analytics
            try:
                data = urllib.urlencode(data_dict)
                response = requests.post(self.ga_collection_url, data=data,headers=headers,timeout=5)
                # signals to queue job is done
                self.queue.task_done()
            except:
                #If error posting dont try again or attempt to fix just discard from queue
                self.queue.task_done()


class GoogleAnalyticsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurable, inherit=True)
    p.implements(p.IRoutes, inherit=True)

    analytics_queue = Queue.Queue()

    def configure(self, config):
        '''Load config settings for this extension from config file.

        See IConfigurable.

        '''
        # spawn a pool of 5 threads, and pass them queue instance
        for i in range(5):
            t = AnalyticsPostThread(self.analytics_queue)
            t.setDaemon(True)
            t.start()

    def before_map(self, map):
        '''Add new routes that this extension's controllers handle.

        See IRoutes.

        '''
        # Helpers to reduce code clutter
        GET_POST = dict(method=['GET', 'POST'])
        # /api ver 3 or none
        with SubMapper(map, controller='ckanext.data_qld.google_analytics_controller:GoogleAnalyticsApiController', path_prefix='/api{ver:/3|}', ver='/3') as m:
            m.connect('/action/{api_action}', action='action', conditions=GET_POST)

        return map


