from ckan.common import _, c

import helpers
import ckan.authz as authz
import ckan.logic.auth as logic_auth


def member_create(context, data_dict):
    """
    This code is largely borrowed from /src/ckan/ckan/logic/auth/create.py
    With a modification to allow users to add datasets to any group
    :param context:
    :param data_dict:
    :return:
    """
    group = logic_auth.get_group_object(context, data_dict)
    user = context['user']

    # User must be able to update the group to add a member to it
    permission = 'update'
    # However if the user is member of group then they can add/remove datasets
    if not group.is_organization and data_dict.get('object_type') == 'package':
        permission = 'manage_group'

    if c.controller in ['package', 'dataset'] and c.action in ['groups']:
        authorized = helpers.user_has_admin_access(True)
    else:
        authorized = authz.has_user_permission_for_group_or_org(group.id,
                                                                user,
                                                                permission)
    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit group %s') %
                        (str(user), group.id)}
    else:
        return {'success': True}


def has_user_permission_for_some_org(context, data_dict):
    user = context.get('user', '')
    permission = data_dict.get('permission', '')
    if authz.has_user_permission_for_some_org(user, permission):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User {0} has no {1} permission for any organisation'.format(user, permission))}


def has_user_permission_for_org(context, data_dict):
    user = context.get('user', '')
    org_id = data_dict.get('org_id', '')
    permission = data_dict.get('permission', '')
    if authz.has_user_permission_for_group_or_org(org_id, user, permission):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User {0} is not authorized to {1} for organisation {2}'.format(user, permission, org_id))}