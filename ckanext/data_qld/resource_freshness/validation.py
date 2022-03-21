# encoding: utf-8

import ckantoolkit as tk
import ckan.lib.navl.dictization_functions as df
import datetime as dt

from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers
from ckanext.data_qld import helpers as data_qld_helpers

unflatten = df.unflatten
missing = tk.missing
StopOnError = tk.StopOnError
get_validator = tk.get_validator
_ = tk._
get_action = tk.get_action
h = tk.h


def validate_next_update_due(keys, flattened_data, errors, context):
    '''
    Validate the next due date according the `update_frequency` input
    '''
    if data_qld_helpers.is_delete_request():
        return

    data = unflatten(flattened_data)
    key, = keys
    next_update_due = data.get(key)
    update_frequency = data.get('update_frequency')

    current_next_update_due = None
    current_update_frequency = None
    if data.get('id'):
        # # Dataset already exists, check current values to see if there are any updates to validate
        if context.get('package'):
            # Package model object should be set in 'package_update' action
            extras = context.get('package').as_dict().get('extras', {})
            current_next_update_due = extras.get('next_update_due')
            current_update_frequency = extras.get('update_frequency')
        else:
            # If for some reason it is not use package_show
            data_dict = get_action('package_show')(context, {"id": data.get('id')})
            current_next_update_due = data_dict.get('next_update_due')
            current_update_frequency = data_dict.get('update_frequency')

        if (next_update_due == current_next_update_due) and (update_frequency == current_update_frequency):
            # No updates to validate
            return

    if update_frequency in resource_freshness_helpers.get_update_frequencies():
        if next_update_due:
            next_update_due = get_validator('isodate')(next_update_due, {})
            today = dt.datetime.now(h.get_display_timezone())
            if next_update_due.date() <= today.date():
                errors[keys].append(_("Valid date in the future is required"))
        elif data_qld_helpers.is_api_request() or not current_next_update_due:
            flattened_data[keys] = resource_freshness_helpers.recalculate_next_update_due_date(flattened_data, update_frequency, errors, context)
        else:
            errors[keys].append(_('Missing value'))
            raise StopOnError
    else:
        flattened_data[keys] = None


def validate_nature_of_change_data(keys, flattened_data, errors, context):
    '''
    Validate the nature of change data
    '''
    if data_qld_helpers.is_delete_request():
        return

    data = unflatten(flattened_data)
    res, index, key = keys
    resource = data.get(res, [])[index]

    update_frequency = data.get('update_frequency')
    nature_of_change = resource.get(key)

    if resource.get('id'):
        if update_frequency not in resource_freshness_helpers.get_update_frequencies():
            return

        # Resource updated
        # Only validate the current resource being updated unless its coming from the API
        # The resource_data_updated value is set in  the 'before_update' IResource interface method 'check_resource_data'
        resource_data_updated = context.get('resource_data_updated', {})
        api_request = data_qld_helpers.is_api_request()
        if api_request or resource_data_updated and resource_data_updated.get('id') == resource.get('id'):
            if api_request or resource_data_updated.get('data_updated', False) is True:
                # Resource data has been updated or the call is from the API so the nature_of_change validation is required
                if not nature_of_change or nature_of_change is missing:
                    errors[keys].append(_('Missing value'))
                    raise StopOnError

            # If nature_of_change is selected check value to see if the correct nature of change provided
            if nature_of_change == 'add-new-time-series' and update_frequency in resource_freshness_helpers.get_update_frequencies():
                resource_freshness_helpers.recalculate_next_update_due_date(flattened_data, update_frequency, errors, context)
    else:
        # Resource created
        if (update_frequency in resource_freshness_helpers.get_update_frequencies() and data.get('state') == 'active'):
            resource_freshness_helpers.recalculate_next_update_due_date(flattened_data, update_frequency, errors, context)
        # Should not have a nature_of_change so remove it
        flattened_data.pop(keys, None)


def data_last_updated(keys, flattened_data, errors, context):
    '''
    Validate last data updated
    '''
    if data_qld_helpers.is_delete_request():
        return

    key, = keys
    data = unflatten(flattened_data)
    if not data.get('id'):
        # New dataset being created, there will be no resources so exit
        flattened_data[keys] = None
        return
    # Get package from context if it exists because the validator doesn't have the resources when a dataset is updated
    if context.get('package'):
        # Package model object should be set in 'package_update' action
        data_dict = context.get('package').as_dict()
        current_data_last_updated = data_dict.get('extras', {}).get(key)
        resources = data_dict.get('resources', [])
    else:
        # If for some reason it is not use package_show
        data_dict = get_action('package_show')(context, {"id": data.get('id')})
        current_data_last_updated = data_dict.get(key)
        resources = data_dict.get('resources', [])
    data_last_updated = get_validator('isodate')(current_data_last_updated, context) if current_data_last_updated else None
    # Cycle through the resources to compare data_last_updated field with last_modified
    for resource in resources:
        last_modified = get_validator('isodate')(resource.get('last_modified') or resource.get('created'), context)
        if data_last_updated is None or last_modified > data_last_updated:
            data_last_updated = last_modified

    flattened_data[keys] = data_last_updated.isoformat() if isinstance(data_last_updated, dt.datetime) else None


def last_modified(keys, flattened_data, errors, context):
    '''
    Validate and recalculate the last_modified value of the resource
    '''
    if data_qld_helpers.is_delete_request():
        return
    data = unflatten(flattened_data)
    res, index, key = keys
    resource = data.get(res, [])[index]

    if resource.get('id'):
        # If existing resource, we need to check if the resource is updated before
        resource_data_updated = context.get('resource_data_updated', {})
        api_request = data_qld_helpers.is_api_request()
        if api_request or resource_data_updated and resource_data_updated.get('id') == resource.get('id'):
            if api_request or resource_data_updated.get('data_updated', False) is True:
                # Resource data has been updated or the call is from the API so the nature_of_change validation is required
                resource_freshness_helpers.update_last_modified(flattened_data, index, errors, context)
    else:
        # For new resource we update the last modified
        resource_freshness_helpers.update_last_modified(flattened_data, index, errors, context)
