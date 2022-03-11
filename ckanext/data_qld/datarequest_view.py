# encoding: utf-8

from flask import Blueprint

from ckanext.data_qld.controller_functions import open_datarequest

import constants


_datarequest = Blueprint(
    u'data_qld_datarequest',
    __name__,
    url_prefix='/' + constants.DATAREQUESTS_MAIN_PATH
)


_datarequest.add_url_rule(u'/open/<id>', 'open', view_func=open_datarequest)


def get_blueprints():
    return [_datarequest]
