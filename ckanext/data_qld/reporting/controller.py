# encoding: utf-8

from ckantoolkit import BaseController

from controller_functions import datarequests, datasets, export, index


class ReportingController(BaseController):

    def index(self):
        return index()

    def export(self):
        return export()

    def datasets(self, org_id, metric):
        return datasets(org_id, metric)

    def datarequests(self, org_id, metric):
        return datarequests(org_id, metric)
