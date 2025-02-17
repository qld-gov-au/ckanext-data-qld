# encoding: utf-8

import ckan.authz as authz
from ckantoolkit import _, auth_allow_anonymous_access


@auth_allow_anonymous_access
def has_user_permission_for_some_org(context, data_dict):
    user = context.get('user', '')
    user_obj = context.get('auth_user_obj', None)
    permission = data_dict.get('permission', '')
    if user_obj and user_obj.get('sysadmin') or authz.has_user_permission_for_some_org(user, permission):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User {0} has no {1} permission for any organisation'.format(user, permission))}


@auth_allow_anonymous_access
def has_user_permission_for_org(context, data_dict):
    user = context.get('user', '')
    user_obj = context.get('auth_user_obj', None)
    org_id = data_dict.get('org_id', '')
    permission = data_dict.get('permission', '')
    if user_obj and user_obj.get('sysadmin') or authz.has_user_permission_for_group_or_org(org_id, user, permission):
        return {'success': True}
    else:
        return {'success': False,
                'msg': _('User {0} is not authorized to {1} for organisation {2}'.format(user, permission, org_id))}
