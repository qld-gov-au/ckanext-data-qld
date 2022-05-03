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
    the resource_visible value and user.
    """
    is_sysadmin = user_obj is not None and user_obj.sysadmin
    if not is_sysadmin:
        resources = data_dict.get('resources', [])
        # if user is NOT Member, Editor, Admin remove the resource.
        if not has_user_permission_for_org(data_dict.get('owner_org'), user_obj, 'read'):
            # Loop through each resource and remove the resource when the below condition is True
            # If resource_visible is `FALSE` or
            # resource_visible is `TRUE` and governance_acknowledgement is `NO` and de_identified_data is `YES`
            de_identified_data = data_dict.get('de_identified_data', 'NO')
            for resource in list(resources):
                hide_resource = resource.get('resource_visible', 'TRUE') == 'FALSE'
                if not hide_resource:
                    governance_acknowledgement = resource.get('governance_acknowledgement', 'NO')
                    hide_resource = governance_acknowledgement == 'NO' and de_identified_data == 'YES'

                if hide_resource:
                    resources.remove(resource)
                    data_dict['num_resources'] -= 1

        # if user is NOT Editor, Admin remove the metadata fields the user does not have access to
        if not has_user_permission_for_org(data_dict.get('owner_org'), user_obj, 'create_dataset'):
            # Remove metadata fields the user does not have access to
            for resource in resources:
                resource.pop('resource_visible', None)
                resource.pop('governance_acknowledgement', None)
