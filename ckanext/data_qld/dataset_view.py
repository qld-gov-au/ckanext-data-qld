# encoding: utf-8

import json
import logging

from flask import Blueprint

from ckan.common import g
import ckan.model as model
from ckan.plugins import toolkit as tk
from ckan.views import dataset, resource

import constants

log = logging.getLogger(__name__)
c = tk.c


_dataset = Blueprint(
    u'data_qld_dataset',
    __name__,
    url_prefix=u'/dataset/<id>',
    url_defaults={u'package_type': u'dataset'}
)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': c.user, 'for_view': True,
            'auth_user_obj': c.userobj}


def _get_errors_summary(errors):
    return ', '.join([error for key, error in errors.items()])


def _is_dataset_public(id):
    try:
        tk.get_action('package_show')(_get_context(), {'id': id})
        return True
    except tk.NotFound:
        tk.abort(404, tk._('Dataset not found'))
    except tk.NotAuthorized:
        return False


def dataset_read(package_type, id):
    """
    Override the default CKAN behaviour for private Dataset visibility.
    Instead of displaying "404 Dataset not found" message,
    give unauthenticated users a chance to log in.
    :param id: Package id/name
    :return:
    """
    if not g.user and not _is_dataset_public(id):
        tk.redirect_to(
            tk.url_for('user.login', came_from='/dataset/{id}'.format(id=id))
        )

    return dataset.read(package_type, id)


def resource_read(package_type, id, resource_id):
    """
    Override the default CKAN behaviour for private Dataset Resource visibility.
    Instead of displaying "404 Dataset not found" message,
    give unauthenticated users a chance to log in.
    :param id: Package id/name
    :param resource_id: Resource id
    :return:
    """
    if not g.user and not _is_dataset_public(id):
        tk.redirect_to(
            tk.url_for('user.login',
                       came_from='/dataset/{id}/resource/{resource_id}'.format(id=id, resource_id=resource_id))
        )

    return resource.read(package_type, id, resource_id)


def show_schema(package_type, id, resource_id):
    """ Display the resource validation schema, if any.
    """
    data_dict = {'id': resource_id}
    context = _get_context()

    try:
        tk.check_access(constants.RESOURCE_SHOW, context, data_dict)
        resource = tk.get_action(constants.RESOURCE_SHOW)(context, data_dict)
        schema_data = resource.get('schema')
        c.schema_data = json.dumps(schema_data, indent=2, sort_keys=True)
        return tk.render('schema/show.html')
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Resource %s not found') % resource_id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to view the Data Scheme for the resource %s' % resource_id))


_dataset.add_url_rule(u'', view_func=dataset_read)
_dataset.add_url_rule(u'/resource/<resource_id>', view_func=resource_read)
_dataset.add_url_rule(u'/resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH), view_func=show_schema)


def get_blueprints():
    return [_dataset]
