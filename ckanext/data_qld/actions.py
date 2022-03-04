# encoding: utf-8

import datetime
import logging

from ckan import model
from ckan.lib import base, helpers, mailer
import ckantoolkit as tk
from ckantoolkit import config

from ckanext.datarequests import db, validator

import constants

log = logging.getLogger(__name__)

# Avoid user_show lag
USERS_CACHE = {}


def _get_user(user_id):
    try:
        if user_id in USERS_CACHE:
            return USERS_CACHE[user_id]
        else:
            user = tk.get_action('user_show')({'ignore_auth': True}, {'id': user_id})
            USERS_CACHE[user_id] = user
            return user
    except Exception as e:
        log.warn(e)


def _get_organization(organization_id):
    try:
        organization_show = tk.get_action('organization_show')
        return organization_show({'ignore_auth': True}, {'id': organization_id, 'include_users': True})
    except Exception as e:
        log.warn(e)


def _get_package(package_id):
    try:
        package_show = tk.get_action('package_show')
        return package_show({'ignore_auth': True}, {'id': package_id})
    except Exception as e:
        log.warn(e)


def _dictize_datarequest(datarequest):
    # Transform time
    open_time = str(datarequest.open_time)
    # Close time can be None and the transformation is only needed when the
    # fields contains a valid date
    close_time = datarequest.close_time
    close_time = str(close_time) if close_time else close_time

    # Convert the data request into a dict
    data_dict = {
        'id': datarequest.id,
        'user_id': datarequest.user_id,
        'title': datarequest.title,
        'description': datarequest.description,
        'organization_id': datarequest.organization_id,
        'open_time': open_time,
        'accepted_dataset_id': datarequest.accepted_dataset_id,
        'close_time': close_time,
        'closed': datarequest.closed,
        'user': _get_user(datarequest.user_id),
        'organization': None,
        'accepted_dataset': None,
        'followers': 0,
        'dataset_url': helpers.url_for('datarequest.show', id=datarequest.id, qualified=True)
    }

    if datarequest.organization_id:
        data_dict['organization'] = _get_organization(datarequest.organization_id)

    if datarequest.accepted_dataset_id:
        data_dict['accepted_dataset'] = _get_package(datarequest.accepted_dataset_id)

    data_dict['followers'] = db.DataRequestFollower.get_datarequest_followers_number(
        datarequest_id=datarequest.id)

    if tk.h.closing_circumstances_enabled:
        data_dict['close_circumstance'] = datarequest.close_circumstance
        data_dict['approx_publishing_date'] = datarequest.approx_publishing_date

    return data_dict


def _undictize_datarequest_basic(datarequest, data_dict):
    datarequest.title = data_dict['title']
    datarequest.description = data_dict['description']
    organization = data_dict['organization_id']
    datarequest.organization_id = organization if organization else None
    _undictize_datarequest_closing_circumstances(datarequest, data_dict)


def _undictize_datarequest_closing_circumstances(datarequest, data_dict):
    if tk.h.closing_circumstances_enabled:
        datarequest.close_circumstance = data_dict.get('close_circumstance') or None
        datarequest.approx_publishing_date = data_dict.get('approx_publishing_date') or None


def _send_mail(user_ids, action_type, datarequest, job_title):
    for user_id in user_ids:
        try:
            user_data = model.User.get(user_id)
            extra_vars = {
                'datarequest': datarequest,
                'user': user_data,
                'site_title': config.get('ckan.site_title'),
                'site_url': config.get('ckan.site_url')
            }
            subject = base.render_jinja2('emails/subjects/{0}.txt'.format(action_type), extra_vars)
            body = base.render_jinja2('emails/bodies/{0}.txt'.format(action_type), extra_vars)
            tk.enqueue_job(mailer.mail_user, [user_data, subject, body], title=job_title)
        except Exception:
            logging.exception("Error sending notification to {0}".format(user_id))


def _get_admin_users_from_organisation(datarequest_dict):
    # Data QLD modification.
    users = set([user['id'] for user in datarequest_dict['organization']['users'] if user.get('capacity') == 'admin'])
    return users


# Copied from ckanext.datarequests.actions. Please keep up to date with any extension updates
@tk.chained_action
def create_datarequest(original_action, context, data_dict):
    """
    Action to create a new data request. The function checks the access rights
    of the user before creating the data request. If the user is not allowed
    a NotAuthorized exception will be risen.

    In addition, you should note that the parameters will be checked and an
    exception (ValidationError) will be risen if some of these parameters are
    not valid.

    Data QLD modification
    Will send email notification to users of assigned organisation with admin access

    :param title: The title of the data request
    :type title: string

    :param description: A brief description for your data request
    :type description: string

    :param organiztion_id: The ID of the organization you want to asign the
        data request (optional).
    :type organization_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed,
        followers)
    :rtype: dict
    """

    model = context['model']
    session = context['session']

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.CREATE_DATAREQUEST, context, data_dict)

    # Validate data
    validator.validate_datarequest(context, data_dict)

    # Store the data
    data_req = db.DataRequest()
    _undictize_datarequest_basic(data_req, data_dict)
    data_req.user_id = context['auth_user_obj'].id
    data_req.open_time = datetime.datetime.utcnow()

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    if datarequest_dict['organization']:
        # Data QLD modification
        users = _get_admin_users_from_organisation(datarequest_dict)
        users.discard(context['auth_user_obj'].id)
        _send_mail(users, 'new_datarequest_organisation', datarequest_dict, 'Data Request Created Email')

    return datarequest_dict


#  Copied from ckanext.datarequests.actions. Please keep up to date with any action updates
@tk.chained_action
def update_datarequest(original_action, context, data_dict):
    """
    Action to update a data request. The function checks the access rights of
    the user before updating the data request. If the user is not allowed
    a NotAuthorized exception will be risen.

    In addition, you should note that the parameters will be checked and an
    exception (ValidationError) will be risen if some of these parameters are
    invalid.

    Data QLD modification
    Will send email notification if organisation was changed to users of assigned organisation with admin access

    :param id: The ID of the data request to be updated
    :type id: string

    :param title: The title of the data request
    :type title: string

    :param description: A brief description for your data request
    :type description: string

    :param organiztion_id: The ID of the organization you want to asign the
        data request.
    :type organization_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed,
        followers)
    :rtype: dict
    """

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    if not datarequest_id:
        raise tk.ValidationError(tk._('Data Request ID has not been included'))

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.UPDATE_DATAREQUEST, context, data_dict)

    # Get the initial data
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound(tk._('Data Request %s not found in the data base') % datarequest_id)

    data_req = result[0]

    # Avoid the validator to return an error when the user does not change the title
    context['avoid_existing_title_check'] = data_req.title == data_dict['title']

    # Validate data
    validator.validate_datarequest(context, data_dict)

    # Data QLD modification
    organisation_updated = data_req.organization_id != data_dict['organization_id']
    if organisation_updated:
        unassigned_organisation_id = data_req.organization_id

    # Set the data provided by the user in the data_red
    _undictize_datarequest_basic(data_req, data_dict)

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    if datarequest_dict['organization'] and organisation_updated:
        # Data QLD modification
        # Email Admin users of the assigned organisation
        users = _get_admin_users_from_organisation(datarequest_dict)
        users.discard(context['auth_user_obj'].id)
        _send_mail(users, 'new_datarequest_organisation', datarequest_dict, 'Data Request Assigned Email')
        # Email Admin users of unassigned organisation
        org_dict = {
            'organization': _get_organization(unassigned_organisation_id)
        }
        users = _get_admin_users_from_organisation(org_dict)
        users.discard(context['auth_user_obj'].id)
        _send_mail(users, 'unassigned_datarequest_organisation', datarequest_dict, 'Data Request Unassigned Email')

    return datarequest_dict


#  Copied from ckanext.datarequests.actions. Please keep up to date with any action updates
@tk.chained_action
def close_datarequest(original_action, context, data_dict):
    """
    Action to close a data request. Access rights will be checked before
    closing the data request. If the user is not allowed, a NotAuthorized
    exception will be risen.

    Data QLD modification
    Will send email notification to the data request creator

    :param id: The ID of the data request to be closed
    :type id: string

    :param accepted_dataset_id: The ID of the dataset accepted as solution
        for this data request
    :type accepted_dataset_id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed,
        followers)
    :rtype: dict

    """

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError(tk._('Data Request ID has not been included'))

    # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.CLOSE_DATAREQUEST, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)
    if not result:
        raise tk.ObjectNotFound(tk._('Data Request %s not found in the data base') % datarequest_id)

    # Validate data
    validator.validate_datarequest_closing(context, data_dict)

    data_req = result[0]

    # Was the data request previously closed?
    if data_req.closed:
        raise tk.ValidationError([tk._('This Data Request is already closed')])

    data_req.closed = True
    data_req.accepted_dataset_id = data_dict.get('accepted_dataset_id') or None
    data_req.close_time = datetime.datetime.utcnow()
    _undictize_datarequest_closing_circumstances(data_req, data_dict)

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    # Mailing
    users = [data_req.user_id]
    _send_mail(users, 'close_datarequest_creator', datarequest_dict, 'Data Request Closed Send Email')

    return datarequest_dict


def open_datarequest(context, data_dict):
    """
    Action to open a data request. Access rights will be checked before
    opening the data request. If the user is not allowed, a NotAuthorized
    exception will be risen.

    :param id: The ID of the data request to be closed
    :type id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed,
        followers)
    :rtype: dict

    """

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError(tk._('Data Request ID has not been included'))

        # Init the data base
    db.init_db(model)

    # Check access
    tk.check_access(constants.OPEN_DATAREQUEST, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)

    if not result:
        raise tk.ObjectNotFound(tk._('Data Request %s not found in the data base') % datarequest_id)

    data_req = result[0]
    data_req.closed = False
    data_req.accepted_dataset_id = None
    data_req.close_time = None
    if tk.h.closing_circumstances_enabled:
        data_req.close_circumstance = None
        data_req.approx_publishing_date = None

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    # Mailing
    users = [data_req.user_id]
    # Creator email
    _send_mail(users, 'open_datarequest_creator', datarequest_dict, 'Data Request Opened Creator Email')
    if datarequest_dict['organization']:
        users = _get_admin_users_from_organisation(datarequest_dict)
        # Admins of organisation email
        _send_mail(users, 'open_datarequest_organisation', datarequest_dict, 'Data Request Opened Admins Email')

    return datarequest_dict
