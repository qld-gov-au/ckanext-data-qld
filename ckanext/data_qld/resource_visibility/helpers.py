import ckan.plugins.toolkit as toolkit
import logging

from ckan import authz
from ckan.model.package import Package

h = toolkit.h
get_action = toolkit.get_action
request = toolkit.request
log = logging.getLogger(__name__)


def get_package_dict(id, use_get_action=True):
    """
    Return package dict.
    """
    if len(id) == 0:
        id = request.path.split('/')[-1]

    try:
        if use_get_action:
            return get_action('package_show')({}, {'name_or_id': id})
        else:
            pkg = Package.get(id)
            if pkg:
                return pkg.as_dict()
    except Exception as e:
        log.error(str(e))

    return {}


def get_select_field_options(field_name, field_schema='resource_fields'):
    """
    Return a list of select options.
    """
    schema = h.scheming_get_dataset_schema('dataset')

    for field in schema.get(field_schema, []):
        if field.get('field_name') == field_name and field.get('choices', None):
            return h.scheming_field_choices(field)

    return []


def user_has_org_role(org_id, user_obj):
    """
    Return None if user doesn't role in the organization.
    """
    if user_obj is None:
        return False

    return authz.users_role_for_group_or_org(org_id, user_obj.name) is not None


def process_resources(data_dict, user_obj):
    """
    Show or hide resources based on
    the resource_visibility value and user.
    """
    # Loop each resources,
    # If resource is `Resource NOT visible/Pending acknowledgement` and
    # if user is NOT Members, Editors, Admins or sysadmin, remove the resource.
    is_sysadmin = user_obj is not None and user_obj.sysadmin

    if not is_sysadmin:
        if not user_has_org_role(data_dict.get('owner_org', None), user_obj):
            resources = data_dict.get('resources', [])
            options = get_select_field_options('resource_visibility')

            for index, resource in enumerate(resources):
                resource_visibility = resource.get('resource_visibility', '')

                # Value of options[2] == Resource NOT visible/Pending acknowledgement.
                if resource_visibility == options[2].get('value') or len(resource_visibility) == 0:
                    data_dict.get('resources').pop(index)
                    data_dict['num_resources'] -= 1


def process_resource_visibility(resource_dict):
    """
    Remove resource_visibility value from dict
    if current user doesn't have access to it.
    """
    if not show_resource_visibility(resource_dict) and 'resource_visibility' in resource_dict:
        del resource_dict['resource_visibility']


def show_resource_visibility(resource_dict):
    """
    Return False if the user does not have
    admin, editor, or sysadmin access to the datasets organisation.
    """
    user_obj = toolkit.g.userobj
    if user_obj is not None:
        is_sysadmin = user_obj.sysadmin
        if is_sysadmin:
            return True

        # Load package to get the org of current resource.
        # Not able to use package_show as it will thrown max recursion depth exceeded.
        pkg_dict = get_package_dict(resource_dict.get('package_id'), False)

        has_org_admin_editor_access = h.data_qld_user_has_admin_editor_org_access(pkg_dict.get('owner_org'), user_obj.name)
        if has_org_admin_editor_access:
            return True

    return False
