# encoding: utf-8

import flask
import six

from controller_functions import datarequests, datasets, export as export_helper, index


def export():
    return_value, headers = export_helper()
    if headers and isinstance(headers, dict):
        response = flask.make_response(return_value)
        for key, value in six.iteritems(headers):
            response.headers[key] = value
        return response
    else:
        return return_value


blueprint = flask.Blueprint(
    u'data_qld_reporting',
    __name__,
    url_prefix='/dashboard/reporting'
)

blueprint.add_url_rule(u'', view_func=index)
blueprint.add_url_rule(u'/export', view_func=export)
blueprint.add_url_rule(u'/datasets/<org_id>/<metric>', view_func=datasets)
blueprint.add_url_rule(u'/datarequests/<org_id>/<metric>', view_func=datarequests)
