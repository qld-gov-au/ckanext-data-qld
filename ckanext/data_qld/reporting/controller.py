# encoding: utf-8

from ckantoolkit import BaseController

from ckanext.data_qld import controller_functions


class ReportingController(BaseController):

    def index(self):
        return controller_functions.reporting_index()

    def export(self):
        return controller_functions.export_reports()

    def datasets(self, org_id, metric):
        return controller_functions.datasets(org_id, metric)

    def datarequests(self, org_id, metric):
        return controller_functions.datarequests(org_id, metric)
