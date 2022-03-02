# encoding: utf-8

import json
import logging

from flask import Blueprint

import ckan.model as model
from ckan.plugins.toolkit import _, abort, c, check_access, g, get_action,\
    NotAuthorized, ObjectNotFound, render

import constants
import helpers

log = logging.getLogger(__name__)


_dataset = Blueprint(
    u'data_qld_dataset',
    __name__,
    url_prefix=u'/dataset/<id>',
    url_defaults={u'package_type': u'dataset'}
)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': g.user, 'for_view': True,
            'auth_user_obj': helpers.get_user()}


def show_schema(package_type, id, resource_id):
    """ Display the resource validation schema, if any.
    """
    data_dict = {'id': resource_id}
    context = _get_context()

    try:
        check_access(constants.RESOURCE_SHOW, context, data_dict)
        resource = get_action(constants.RESOURCE_SHOW)(context, data_dict)
        schema_data = resource.get('schema')
        c.schema_data = json.dumps(schema_data, indent=2, sort_keys=True)
        return render('schema/show.html')
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Resource %s not found') % resource_id)
    except NotAuthorized as e:
        log.warn(e)
        abort(403, _('You are not authorized to view the Data Scheme for the resource %s' % resource_id))


_dataset.add_url_rule(u'/resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH),
                      view_func=show_schema)


def get_blueprints():
    return [_dataset]
