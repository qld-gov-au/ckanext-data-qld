# encoding: utf-8

from ckantoolkit import BaseController

from .controller_functions import (
    open_datarequest,
    show_resource_schema as show_resource_schema_view,
    show_package_schema as show_package_schema_view,
)


class DataQldUI(BaseController):

    def open_datarequest(self, id):
        return open_datarequest(id)

    def show_resource_schema(self, dataset_id, resource_id):
        return show_resource_schema_view(dataset_id, resource_id)

    def show_package_schema(self, dataset_id):
        return show_package_schema_view(dataset_id)
