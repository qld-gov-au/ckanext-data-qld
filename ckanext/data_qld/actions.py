import ckan.lib.base as base
import ckan.model as model
import ckan.plugins as plugins
import ckan.lib.helpers as helpers
import ckan.lib.mailer as mailer
from pylons import config
import logging
import ckanext.datarequests.db as db
import constants


c = plugins.toolkit.c
log = logging.getLogger(__name__)
tk = plugins.toolkit

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
        return organization_show({'ignore_auth': True}, {'id': organization_id})
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
        'dataset_url': helpers.url_for(controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI', action='show', id=datarequest.id, qualified=True)
    }

    if datarequest.organization_id:
        data_dict['organization'] = _get_organization(datarequest.organization_id)

    if datarequest.accepted_dataset_id:
        data_dict['accepted_dataset'] = _get_package(datarequest.accepted_dataset_id)

    data_dict['followers'] = db.DataRequestFollower.get_datarequest_followers_number(
        datarequest_id=datarequest.id)

    return data_dict




def _get_datarequest_involved_users(context, datarequest_dict):

    datarequest_id = datarequest_dict['id']
    new_context = {'ignore_auth': True, 'model': context['model'] }

    # Creator + Followers + People who has commented + Organization Staff
    users = set()
    users.add(datarequest_dict['user_id'])
    list_datarequest_comments = tk.get_action(constants.LIST_DATAREQUESTS)
    users.update([follower.user_id for follower in db.DataRequestFollower.get(datarequest_id=datarequest_id)])
    users.update([comment['user_id'] for comment in list_datarequest_comments(new_context, {'datarequest_id': datarequest_id})])

    if datarequest_dict['organization']:
        users.update([user['id'] for user in datarequest_dict['organization']['users']])
    
    # Notifications are not sent to the user that performs the action
    users.discard(context['auth_user_obj'].id)

    return users


def _send_mail(user_ids, action_type, datarequest):

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

            mailer.mail_user(user_data, subject, body)

        except Exception:
            logging.exception("Error sending notification to {0}".format(user_id))


def open_datarequest(context, data_dict):
    '''
    Action to open a data request. Access rights will be checked before
    opening the data request. If the user is not allowed, a NotAuthorized
    exception will be risen.

    :param id: The ID of the data request to be closed
    :type id: string    

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed, 
        followers)
    :rtype: dict

    '''

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

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    # Mailing
    users = [data_req.user_id]    
    _send_mail(users, 'open_datarequest_creator', datarequest_dict)
    if datarequest_dict['organization']:
        users = set([user['id'] for user in datarequest_dict['organization']['users'] if user.get('capacity') == 'admin']) 
        _send_mail(users, 'open_datarequest_organisation', datarequest_dict)
    
    return datarequest_dict
   