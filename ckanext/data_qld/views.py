# encoding: utf-8

import json
import logging

from flask import Blueprint

from ckan.common import _, g
from ckan.logic import get_action, NotFound, NotAuthorized
import ckan.lib.base as base
import ckan.model as model
import ckan.plugins as plugins
from ckan.views import dataset, resource

import constants

abort = base.abort
log = logging.getLogger(__name__)
tk = plugins.toolkit
c = tk.c


_dataset = Blueprint(
    u'data_qld_dataset',
    __name__,
    url_prefix=u'/dataset/<id>',
    url_defaults={u'package_type': u'dataset'}
)

_datarequest = Blueprint(
    u'data_qld_datarequest',
    __name__,
    url_prefix='/' + constants.DATAREQUESTS_MAIN_PATH
)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': c.user, 'for_view': True,
            'auth_user_obj': c.userobj}


def _get_errors_summary(errors):
    return ', '.join([error for key, error in errors.items()])


def _is_dataset_public(id):
    try:
        get_action('package_show')(_get_context(), {'id': id})
        return True
    except NotFound:
        abort(404, _('Dataset not found'))
    except NotAuthorized:
        return False


def dataset_read(package_type, id):
    """
    Override the default CKAN behaviour for private Dataset visibility.
    Instead of displaying "404 Dataset not found" message,
    give unauthenticated users a chance to log in.
    :param id: Package id/name
    :return:
    """
    log.debug("Blueprint dataset_read")
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
    log.debug("Blueprint resource_read")
    if not g.user and not _is_dataset_public(id):
        tk.redirect_to(
            tk.url_for('user.login',
                       came_from='/dataset/{id}/resource/{resource_id}'.format(id=id, resource_id=resource_id))
        )

    return resource.read(package_type, id, resource_id)


def show_schema(package_type, id, resource_id):
    """ Display the resource validation schema, if any.
    """
    log.debug("Blueprint show_schema")
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


def open_datarequest(id):
    """ Opens a closed Data Request.
    """
    log.debug("Blueprint open_datarequest")
    data_dict = {'id': id}
    context = _get_context()

    # Basic initialization
    c.datarequest = {}
    try:
        tk.check_access(constants.OPEN_DATAREQUEST, context, data_dict)
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(context, data_dict)

        if c.datarequest.get('closed', False) is False:
            tk.abort(403, tk._('This data request is already open'))
        else:
            data_dict = {}
            data_dict['id'] = id
            data_dict['organization_id'] = c.datarequest.get('organization_id')

            tk.get_action(constants.OPEN_DATAREQUEST)(context, data_dict)
            tk.redirect_to('datarequest.show', id=data_dict['id'])
    except tk.ValidationError as e:
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        tk.abort(403, errors_summary)
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to open the Data Request %s' % id))


_dataset.add_url_rule(u'', view_func=dataset_read)
_dataset.add_url_rule(u'/resource/<resource_id>', view_func=resource_read)
_dataset.add_url_rule(u'/resource/<resource_id>/{}/show'.format(constants.SCHEMA_MAIN_PATH), view_func=show_schema)

_datarequest.add_url_rule(u'/open/<id>', view_func=open_datarequest)


def get_blueprints():
    return [_dataset, _datarequest]
