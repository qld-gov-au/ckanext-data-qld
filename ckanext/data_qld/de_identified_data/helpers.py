import logging

from ckan import authz

log = logging.getLogger(__name__)


def process_de_identified_data_dict(data_dict, user_obj):
    """
    Remove de_identified_data value from dict
    if current user doesn't have access to it.
    """
    if not show_de_identified_data(data_dict, user_obj):
        return data_dict.pop('de_identified_data', None)
    if data_dict.get('de_identified_data', None) is None:
        # Add default value to NO.
        data_dict['de_identified_data'] = 'NO'


def user_has_admin_editor_org_access(group_id, user_name):
    """
    Return False if the user does not have
    admin, editor, or sysadmin access to the datasets organisation.
    """
    return authz.has_user_permission_for_group_or_org(group_id, user_name, 'create_dataset')


def show_de_identified_data(data_dict, user_obj):
    """
    Return False if current user doesn't have access to it.
    """
    if user_obj is not None:
        is_sysadmin = user_obj.sysadmin
        if is_sysadmin:
            return True

        has_org_admin_editor_access = user_has_admin_editor_org_access(data_dict.get('owner_org', None), user_obj.name)
        if has_org_admin_editor_access:
            return True

    return False
