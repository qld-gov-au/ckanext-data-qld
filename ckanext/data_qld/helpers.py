import ckan.plugins.toolkit as toolkit
from bs4 import BeautifulSoup
from pylons import config


def is_user_sysadmin(user=None):
    """Returns True if authenticated user is sysadmim

    :rtype: boolean

    """
    if user is None:
        user = toolkit.c.userobj
    return user is not None and user.sysadmin


def user_has_admin_access(include_editor_access):
    user = toolkit.c.userobj
    # If user is "None" - they are not logged in.
    if user is None:
        return False
    if is_user_sysadmin(user):
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


def organisation_list():
    """Returns a list of organisations with all the organisation fields

    :rtype: Array of organisations

    """
    return toolkit.get_action('organization_list')(data_dict={'all_fields': True})


def datarequest_suggested_description():
    """Returns a datarequest suggested description from admin config

    :rtype: string

    """
    return config.get('ckanext.data_qld.datarequest_suggested_description', '')


def format_activity_data(data):
    """Returns the activity data with actors username replaced with Publisher for non-editor/admin/sysadmin users

    :rtype: string

    """
    if (user_has_admin_access(True)):
        return data

    soup = BeautifulSoup(data, 'html.parser')

    for actor in soup.select(".actor"):
        actor.string = 'Publisher'
        # the img element is removed from actor span so need to move actor span to the left to fill up blank space
        actor['style'] = 'margin-left:-40px'

    return soup.prettify(formatter="html5")


# Data.Qld specific comments helper functions

def get_content_type_comments_badge(dataset_id, content_type):
    return toolkit.render_snippet('snippets/badge.html',
                                  {'count': toolkit.h.get_comment_count_for_dataset(dataset_id,
                                                                                    content_type)})


def resource_formats(field):
    """Returns a list of resource formats from admin config

    :rtype: Array resource formats

    """
    resource_formats = config.get('ckanext.data_qld.resource_formats', '').split('\r\n')
    return [{'value': resource_format.strip().upper(), 'label': resource_format.strip().upper()}
            for resource_format in resource_formats]
