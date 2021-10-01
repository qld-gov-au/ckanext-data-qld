import ckan.logic as logic
import ckan.plugins.toolkit as toolkit

from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers
from datetime import datetime, timedelta


@toolkit.side_effect_free
def dataset_due_to_publishing(context, data_dict):
    today = datetime.today()
    start_date = (today + timedelta(15)).strftime('%Y-%m-%d')
    end_date = (today + timedelta(21)).strftime('%Y-%m-%d')

    return toolkit.get_action('package_search')(context, {
        'rows': 1000,
        'fq': 'update_frequency:(annually OR half-yearly OR quarterly OR monthly)+next_update_due:[' + start_date + ' TO ' + end_date + ']'
    })


@toolkit.side_effect_free
def dataset_overdue(context, data_dict):
    today = datetime.today()
    start_date = (today - timedelta(7)).strftime('%Y-%m-%d')
    end_date = (today - timedelta(1)).strftime('%Y-%m-%d')

    return toolkit.get_action('package_search')(context, {
        'rows': 1000,
        'fq': 'update_frequency:(annually OR half-yearly OR quarterly OR monthly)+next_update_due:[' + start_date + ' TO ' + end_date + ']'
    })


@toolkit.side_effect_free
def process_dataset_due_to_publishing(context, data_dict):
    # Only sysadmin can access.
    user_obj = context.get('auth_user_obj', None)
    is_sysadmin = user_obj and user_obj.sysadmin
    if not user_obj or not is_sysadmin:
        raise logic.NotAuthorized

    resource_freshness_helpers.process_email_notification_for_dataset_due_to_publishing()


@toolkit.side_effect_free
def process_dataset_overdue(context, data_dict):
    # Only sysadmin can access.
    user_obj = context.get('auth_user_obj', None)
    is_sysadmin = user_obj and user_obj.sysadmin
    if not user_obj or not is_sysadmin:
        raise logic.NotAuthorized

    resource_freshness_helpers.process_email_notification_for_dataset_overdue()
