# encoding: utf-8

from flask import Blueprint

from controller_functions import datarequests, datasets, export, index


blueprint = Blueprint(
    u'data_qld_reporting',
    __name__,
    url_prefix='/dashboard/reporting'
)

blueprint.add_url_rule(u'', view_func=index)
blueprint.add_url_rule(u'/export', view_func=export)
blueprint.add_url_rule(u'/datasets/<org_id>/<metric>', view_func=datasets)
blueprint.add_url_rule(u'/datarequests/<org_id>/<metric>', view_func=datarequests)
