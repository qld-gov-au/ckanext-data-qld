# encoding: utf-8

import logging
import json

from ckantoolkit import _, abort, c, check_access, g, get_action, \
    redirect_to, NotAuthorized, ObjectNotFound, url_for, \
    ValidationError

from ckan import model

from . import helpers
from .constants import OPEN_DATAREQUEST, RESOURCE_SHOW, SHOW_DATAREQUEST, PACKAGE_SHOW


log = logging.getLogger(__name__)


def _get_errors_summary(errors):
    errors_summary = ''

    for key, error in errors.items():
        errors_summary = ', '.join(error)

    return errors_summary


def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': helpers.get_user()
    }


def open_datarequest(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic initialization
    c.datarequest = {}
    try:
        check_access(OPEN_DATAREQUEST, context, data_dict)
        c.datarequest = get_action(SHOW_DATAREQUEST)(context, data_dict)

        if c.datarequest.get('closed', False) is False:
            return abort(403, _('This data request is already open'))
        else:
            data_dict = {}
            data_dict['id'] = id
            data_dict['organization_id'] = c.datarequest.get('organization_id')

            get_action(OPEN_DATAREQUEST)(context, data_dict)
            return redirect_to(url_for('datarequest.show', id=data_dict['id']))
    except ValidationError as e:
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return abort(403, errors_summary)
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Data Request %s not found') % id)
    except NotAuthorized as e:
        log.warn(e)
        return abort(
            403, _('You are not authorized to open the Data Request %s' % id))


def show_resource_schema(dataset_id, resource_id):
    context = _get_context()

    data = _get_resource_data(resource_id, context)
    schema_data = data.get('schema')

    if not schema_data:
        return abort(404, _('Schema not found'))

    return json.dumps(schema_data, indent=4)


def _get_resource_data(resource_id, context):
    data_dict = {"id": resource_id}

    try:
        check_access(RESOURCE_SHOW, context, data_dict)
        res_data = get_action(RESOURCE_SHOW)(context, data_dict)
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Resource %s not found') % resource_id)
    except NotAuthorized as e:
        log.warn(e)
        return abort(
            403,
            _('You are not authorized to view the Data Scheme for the resource %s'
              % resource_id))

    return res_data


def show_package_schema(dataset_id):
    context = _get_context()

    data = _get_package_data(dataset_id, context)
    schema_data = data.get('default_data_schema')

    if not schema_data:
        return abort(404, _('Schema not found'))

    return json.dumps(schema_data, indent=4)


def _get_package_data(dataset_id, context):
    data_dict = {"id": dataset_id}

    try:
        check_access(PACKAGE_SHOW, context, {"id": dataset_id})
        pkg_data = get_action(PACKAGE_SHOW)(context, data_dict)
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Package %s not found') % dataset_id)
    except NotAuthorized as e:
        log.warn(e)
        return abort(
            403,
            _('You are not authorized to view the Data Scheme for the package %s'
              % dataset_id))

    return pkg_data
