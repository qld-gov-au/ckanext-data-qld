# encoding: utf-8

from flask import Blueprint

from ckanext.data_qld import constants
from ckanext.data_qld.controller_functions import open_datarequest, show_schema


blueprint = Blueprint(
    u'data_qld',
    __name__
)

blueprint.add_url_rule('/%s/open/<id>' % constants.DATAREQUESTS_MAIN_PATH, view_func=open_datarequest, methods=('GET', 'POST'))
blueprint.add_url_rule('/dataset/<dataset_id>/resource/<resource_id>/%s/show/' % constants.SCHEMA_MAIN_PATH, view_func=show_schema, methods=('GET',))


def get_blueprints():
    return [blueprint]
