# encoding: utf-8

from flask import Blueprint

from ckanext.data_qld.controller_functions import open_datarequest, show_schema

import constants


blueprint = Blueprint(
    u'data_qld',
    __name__
)


blueprint.add_url_rule(
    u'/{}/open/<id>'.format(constants.DATAREQUESTS_MAIN_PATH),
    'open_datarequest', view_func=open_datarequest)
blueprint.add_url_rule(
    u'/dataset/resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH),
    'show_schema', view_func=show_schema)


def get_blueprints():
    return [blueprint]
