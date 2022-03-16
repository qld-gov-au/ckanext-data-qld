# encoding: utf-8

from flask import Blueprint

from ckanext.data_qld import controller_functions

import constants


blueprint = Blueprint(
    u'data_qld',
    __name__
)


blueprint.add_url_rule(
    u'/{}/open/<id>'.format(constants.DATAREQUESTS_MAIN_PATH),
    'open_datarequest', view_func=controller_functions.open_datarequest)
blueprint.add_url_rule(
    u'/dataset/<dataset_id>resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH),
    'show_schema', view_func=controller_functions.show_schema)

reporting = Blueprint(
    u'data_qld_reporting',
    __name__,
    url_prefix='/dashboard/reporting'
)

reporting.add_url_rule(
    u'', 'index', view_func=controller_functions.reporting_index)
reporting.add_url_rule(
    u'/export',
    'export', view_func=controller_functions.export_reports)
reporting.add_url_rule(
    u'/datasets/<org_id>/<metric>',
    'datasets', view_func=controller_functions.datasets)
reporting.add_url_rule(
    u'/datarequests/<org_id>/<metric>',
    'datarequests', view_func=controller_functions.datarequests)


def get_blueprints():
    return [blueprint, reporting]
