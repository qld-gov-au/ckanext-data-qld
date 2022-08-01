# encoding: utf-8

import six

from ckantoolkit import BaseController, response

from .controller_functions import datarequests, datasets, export, index


class ReportingController(BaseController):

    def index(self):
        return index()

    def export(self):
        return_value, headers = export()
        if headers and isinstance(headers, dict):
            for key, value in six.iteritems(headers):
                response.headers[key] = value
        return return_value

    def datasets(self, org_id, metric):
        return datasets(org_id, metric)

    def datarequests(self, org_id, metric):
        return datarequests(org_id, metric)
