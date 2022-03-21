# encoding: utf-8

import json
import logging

import ckan.model as model
from ckantoolkit import _, abort, c, check_access, g, get_action, \
    redirect_to, render, NotAuthorized, ObjectNotFound, url_for, \
    ValidationError

from constants import OPEN_DATAREQUEST, RESOURCE_SHOW, SHOW_DATAREQUEST
import helpers

log = logging.getLogger(__name__)


def _get_errors_summary(errors):
    errors_summary = ''

    for key, error in errors.items():
        errors_summary = ', '.join(error)

    return errors_summary


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': g.user, 'auth_user_obj': helpers.get_user()}


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
            return redirect_to(
                url_for('datarequest.show', id=data_dict['id']))
    except ValidationError as e:
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return abort(403, errors_summary)
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Data Request %s not found') % id)
    except NotAuthorized as e:
        log.warn(e)
        return abort(403, _('You are not authorized to open the Data Request %s' % id))


def show_schema(dataset_id, resource_id):
    data_dict = {'id': resource_id}
    context = _get_context()

    try:
        check_access(RESOURCE_SHOW, context, data_dict)
        resource = get_action(RESOURCE_SHOW)(context, data_dict)
        schema_data = resource.get('schema')
        c.schema_data = json.dumps(schema_data, indent=2, sort_keys=True)
        return render('schema/show.html')
    except ObjectNotFound as e:
        log.warn(e)
        return abort(404, _('Resource %s not found') % resource_id)
    except NotAuthorized as e:
        log.warn(e)
        return abort(403, _('You are not authorized to view the Data Scheme for the resource %s' % resource_id))
