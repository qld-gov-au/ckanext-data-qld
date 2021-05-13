# encoding: utf-8

import logging

from flask import Blueprint

import ckan.model as model
from ckan.plugins import toolkit as tk

import constants

log = logging.getLogger(__name__)
c = tk.c


_datarequest = Blueprint(
    u'data_qld_datarequest',
    __name__,
    url_prefix='/' + constants.DATAREQUESTS_MAIN_PATH
)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': c.user, 'auth_user_obj': c.userobj}


def _get_errors_summary(errors):
    return ', '.join([error for key, error in errors.items()])


def open_datarequest(id):
    """ Opens a closed Data Request.
    """
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


_datarequest.add_url_rule(u'/open/<id>', view_func=open_datarequest)


def get_blueprints():
    return [_datarequest]
