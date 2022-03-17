# encoding: utf-8

from flask import Blueprint

from constants import DATAREQUESTS_MAIN_PATH, SCHEMA_MAIN_PATH
from controller_functions import open_datarequest, show_schema


blueprint = Blueprint(
    u'data_qld',
    __name__
)

blueprint.add_url_rule(
    u'/{}/open/<id>'.format(DATAREQUESTS_MAIN_PATH),
    view_func=open_datarequest)
blueprint.add_url_rule(
    u'/dataset/<dataset_id>resource/<resource_id>/{}/show'.format(SCHEMA_MAIN_PATH),
    view_func=show_schema)
