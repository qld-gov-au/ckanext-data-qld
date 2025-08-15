# encoding: utf-8

import flask

import ckan.views.api as core_api

from . import controller_functions


def action(api_action, ver=core_api.API_DEFAULT_VERSION):
    return controller_functions.action(core_api._get_request_data, core_api.action, api_action, ver)


blueprint = flask.Blueprint(
    u'data_qld_google_analytics',
    __name__,
    url_prefix='/api'
)

blueprint.add_url_rule(u'/action/<api_action>', view_func=action, methods=('GET', 'POST'))
blueprint.add_url_rule(u'/<int(min=3, max={0}):ver>/action/<api_action>'.format(core_api.API_MAX_VERSION),
                       view_func=action, methods=('GET', 'POST'))
