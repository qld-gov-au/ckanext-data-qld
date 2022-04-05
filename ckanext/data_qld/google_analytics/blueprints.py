# encoding: utf-8

import flask

from ckan.views.api import _get_request_data, action as core_action, API_DEFAULT_VERSION
from ckantoolkit import get_action

from controller_functions import record_api_action


def action(api_action, ver=API_DEFAULT_VERSION):
    function = get_action(api_action)
    side_effect_free = getattr(function, 'side_effect_free', False)
    request_data = _get_request_data(try_url_params=side_effect_free)
    record_api_action(api_action, request_data)
    return core_action(api_action, ver=ver)


blueprint = flask.Blueprint(
    u'data_qld_google_analytics',
    __name__,
    url_prefix='/api'
)

blueprint.add_url_rule(u'/action/<api_action>', view_func=action, methods=('GET', 'POST'))
blueprint.add_url_rule(u'/<ver>/action/<api_action>', view_func=action, methods=('GET', 'POST'))
