# encoding: utf-8

from ckantoolkit import BaseController

from controller_functions import open_datarequest, show_schema


class DataQldUI(BaseController):

    def open_datarequest(self, id):
        return open_datarequest(id)

    def show_schema(self, dataset_id, resource_id):
        return show_schema(dataset_id, resource_id)
