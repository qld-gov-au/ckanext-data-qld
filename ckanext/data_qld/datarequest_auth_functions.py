# encoding: utf-8

import ckantoolkit as toolkit

import constants
import helpers


@toolkit.chained_auth_function
def update_datarequest(next_auth, context, data_dict):
    # Users part of the default data request organisation or selected organisation who have admin/editor access
    # If Auth returns false call the next_auth function in the chain to check their access
    if user_has_datarequest_admin_access(data_dict.get('id'), True, context):
        return {'success': True}
    else:
        return next_auth(context, data_dict)


@toolkit.chained_auth_function
def close_datarequest(next_auth, context, data_dict):
    # Users part of the default data request organisation or selected organisation who have admin access.
    # If Auth returns false, call the next_auth function in the chain to check their access.
    if user_has_datarequest_admin_access(data_dict.get('id'), False, context):
        return {'success': True}
    else:
        return next_auth(context, data_dict)


def update_datarequest_organisation(context, data_dict):
    # Users part of the default data request organisation or selected organisation who have admin/editor access.
    return {'success': user_has_datarequest_admin_access(data_dict.get('id'), True, context)}


def open_datarequest(context, data_dict):
    # Users part of the default data request organisation or selected organisation who have admin access.
    return {'success': user_has_datarequest_admin_access(data_dict.get('id'), False, context)}


def user_has_datarequest_admin_access(datarequest_id, include_editor_access, context):
    user = helpers.get_user()
    # If user is 'None' - they are not logged in.
    if user is None:
        return False
    if user.sysadmin:
        return True

    groups_admin = user.get_groups('organization', 'admin')
    groups_editor = user.get_groups('organization', 'editor') if include_editor_access else []
    groups_list = groups_admin + groups_editor
    organisation_list = [g for g in groups_list if g.type == 'organization']
    user_has_access = len(organisation_list) > 0
    # New Data Request. Check if user has any admin/editor access
    if not datarequest_id or len(datarequest_id) == 0:
        return user_has_access
    # User has admin/editor access so check if they are a member of the default_organisation_id or datarequest_organisation_id
    elif user_has_access:
        default_organisation_id = helpers.datarequest_default_organisation_id()
        datarequest_organisation_id = toolkit.get_action(constants.SHOW_DATAREQUEST)(context, {'id': datarequest_id}).get('organization_id')
        for organisation in organisation_list:
            print('organisation.id: s%', organisation.id)
            # Is user an admin/editor of the default organisation
            if organisation.id == default_organisation_id:
                return True
            # Is user an admin/editor of the data request selected organisation
            elif organisation.id == datarequest_organisation_id:
                return True

    return False
