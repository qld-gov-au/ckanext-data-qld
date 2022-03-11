# encoding: utf-8

from flask import Blueprint

from ckanext.data_qld.controller_functions import show_schema

import constants


_dataset = Blueprint(
    u'data_qld_dataset',
    __name__,
    url_prefix=u'/dataset/<id>',
    url_defaults={u'package_type': u'dataset'}
)


_dataset.add_url_rule(u'/resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH),
                      view_func=show_schema)


def get_blueprints():
    return [_dataset]
