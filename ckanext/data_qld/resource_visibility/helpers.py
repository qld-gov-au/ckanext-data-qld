# encoding: utf-8

import logging

from ckan.model.package import Package
from ckantoolkit import h, get_action

from ckanext.data_qld import helpers as data_qld_helpers, auth_functions

log = logging.getLogger(__name__)


def get_package_dict(id, use_get_action=True):
    """
    Return package dict.
    """
    if len(id) == 0:
        id = data_qld_helpers.get_request_path().split('/')[-1]

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
    if 'scheming_get_dataset_schema' in h:
        schema = h.scheming_get_dataset_schema('dataset')

        for field in schema.get(field_schema, []):
            if field.get('field_name') == field_name and field.get('choices', None):
                return h.scheming_field_choices(field)

    return []


def has_user_permission_for_org(org_id, user_obj, permission):
    """
    Return False if user doesn't have permission in the organization.
    """
    if user_obj is None:
        return False

    context = {'user': user_obj.name}
    data_dict = {'org_id': org_id, 'permission': permission}
    result = auth_functions.has_user_permission_for_org(context, data_dict)

    return result and result.get('success')


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
        if not has_user_permission_for_org(data_dict.get('owner_org'), user_obj, 'read'):
            resources = data_dict.get('resources', [])
            options = get_select_field_options('resource_visibility')
            de_identified_data = data_dict.get('de_identified_data', 'NO') == 'YES'

            for resource in list(resources):
                resource_visibility = resource.get('resource_visibility', '')
                # Value of options[2] == Resource NOT visible/Pending acknowledgement.
                if resource_visibility == options[2].get('value') if len(options) >= 3 else False \
                        or len(resource_visibility) == 0 and de_identified_data:
                    resources.remove(resource)
                    data_dict['num_resources'] -= 1
                else:
                    # Need to remove the resource visibility field from display
                    # if current user don't have access to it.
                    process_resource_visibility(resource)


def process_resource_visibility(resource_dict):
    """
    Remove resource_visibility value from dict
    if current user doesn't have access to it.
    """
    if 'resource_visibility' in resource_dict and not show_resource_visibility(resource_dict):
        del resource_dict['resource_visibility']


def show_resource_visibility(resource_dict):
    """
    Return False if the user does not have
    admin, editor, or sysadmin access to the datasets organisation.
    """
    user_obj = data_qld_helpers.get_user()
    if user_obj is not None:
        is_sysadmin = user_obj.sysadmin
        if is_sysadmin:
            return True

        # Load package to get the org of current resource.
        # Not able to use package_show as it will thrown max recursion depth exceeded.
        pkg_dict = get_package_dict(resource_dict.get('package_id'), False)
        if has_user_permission_for_org(pkg_dict.get('owner_org'), user_obj, 'create_dataset'):
            return True

    return False
