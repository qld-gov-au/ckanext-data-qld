# encoding: utf-8

from ckan.plugins import toolkit
from ckan.plugins.toolkit import config


def user_has_admin_access(include_editor_access):
    user = toolkit.c.userobj
    # If user is "None" - they are not logged in.
    if user is None:
        return False
    if user.sysadmin:
        return True

    groups_admin = user.get_groups('organization', 'admin')
    groups_editor = user.get_groups('organization', 'editor') if include_editor_access else []
    groups_list = groups_admin + groups_editor
    organisation_list = [g for g in groups_list if g.type == 'organization']
    return len(organisation_list) > 0


def data_driven_application(data_driven_application):
    """Returns True if data_driven_application value equals yes
        Case insensitive

    :rtype: boolean

    """
    if data_driven_application and data_driven_application.lower() == 'yes':
        return True
    else:
        return False


def dataset_data_driven_application(dataset_id):
    """Returns True if the dataset for dataset_id data_driven_application value equals yes
        Case insensitive

    :rtype: boolean

    """
    try:
        package = toolkit.get_action('package_show')(
            data_dict={'id': dataset_id})
    except toolkit.ObjectNotFound:
        return False

    return data_driven_application(package.get('data_driven_application', ''))


def datarequest_default_organisation():
    """Returns the default organisation for data request from the config file
        Case insensitive.

    :rtype: organisation

    """
    default_organisation = config.get('ckan.datarequests.default_organisation')
    try:
        organisation = toolkit.get_action('organization_show')(
            data_dict={
                'id': default_organisation,
                'include_datasets': False,
                'include_dataset_count': False,
                'include_extras': False,
                'include_users': False,
                'include_groups': False,
                'include_tags': False,
                'include_followers': False
            })
    except toolkit.ObjectNotFound:
        toolkit.abort(404,
                      toolkit._('Default Data Request Organisation not found. Please get the sysadmin to set one up'))

    return organisation


def datarequest_default_organisation_id():
    """Returns the default organisation id for data request from the config file

    :rtype: integer

    """
    organisation_id = datarequest_default_organisation().get('id')
    print('datarequest_default_organisation_id: %s', organisation_id)
    return organisation_id


def datarequest_suggested_description():
    """Returns a datarequest suggested description from admin config

    :rtype: string

    """
    return config.get('ckanext.data_qld.datarequest_suggested_description', '')


# Data.Qld specific comments helper functions

def resource_formats(field):
    """Returns a list of resource formats from admin config

    :rtype: Array resource formats

    """
    resource_formats = config.get('ckanext.data_qld.resource_formats', '').split('\r\n')
    return [{'value': resource_format.strip().upper(), 'label': resource_format.strip().upper()}
            for resource_format in resource_formats]


def profanity_checking_enabled():
    """Check to see if YTP comments extension is enabled and `check_for_profanity` is enabled

    :rtype: bool

    """
    return 'ytp_comments' in config.get('ckan.plugins', '') \
           and toolkit.asbool(config.get('ckan.comments.check_for_profanity', False))


def get_request():
    return toolkit.request if hasattr(toolkit.request, 'params') else None


def get_request_action():
    request = get_request()
    return toolkit.get_endpoint()[1] if request else ''


def get_request_path():
    request = get_request()
    return request.path if request else ''


def is_delete_request():
    return get_request_action() == 'delete' or 'package_delete' in get_request_path()


def is_api_request():
    return get_request_action() == 'action' or '/action/' in get_request_path()
