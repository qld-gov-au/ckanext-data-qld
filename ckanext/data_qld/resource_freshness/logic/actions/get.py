# encoding: utf-8

import ckan.logic as logic
import ckantoolkit as toolkit

from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers
from datetime import datetime, timedelta


@toolkit.side_effect_free
def dataset_due_to_publishing(context, data_dict):
    today = datetime.now(toolkit.h.get_display_timezone()).date()
    start_date = data_dict.get('start_date') if data_dict.get('start_date') else (today + timedelta(15)).strftime('%Y-%m-%d')
    end_date = data_dict.get('end_date') if data_dict.get('end_date') else (today + timedelta(21)).strftime('%Y-%m-%d')

    return toolkit.get_action('package_search')(context, {
        'rows': 1000,
        'fq': 'update_frequency:(annually OR half-yearly OR quarterly OR monthly)+next_update_due:[' + start_date + ' TO ' + end_date + ']'
    })


@toolkit.side_effect_free
def dataset_overdue(context, data_dict):
    today = datetime.now(toolkit.h.get_display_timezone()).date()
    start_date = data_dict.get('start_date') if data_dict.get('start_date') else (today - timedelta(6)).strftime('%Y-%m-%d')
    end_date = data_dict.get('end_date') if data_dict.get('end_date') else (today - timedelta(0)).strftime('%Y-%m-%d')

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
