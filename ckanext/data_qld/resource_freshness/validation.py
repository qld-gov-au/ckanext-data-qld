# encoding: utf-8
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import datetime as dt

from ckanext.data_qld.resource_freshness.helpers import helpers as h

unflatten = df.unflatten
missing = tk.missing
StopOnError = tk.StopOnError
get_validator = tk.get_validator
_ = tk._
request = tk.request
get_endpoint = tk.get_endpoint
get_action = tk.get_action


def validate_next_update_due(keys, flattened_data, errors, context):
    '''
    Validate the next due date according the `update_frequency` input
    '''
    data = unflatten(flattened_data)
    key, = keys
    next_update_due = data.get(key)
    update_frequency = data.get('update_frequency')

    if update_frequency in h.get_update_frequencies():
        if next_update_due:
            next_update_due = get_validator('isodate')(next_update_due, {})
            if next_update_due.date() <= dt.date.today():
                errors[keys].append(_("Valid date in the future is required"))
        elif get_endpoint()[1] == 'action':
            flattened_data[keys] = h.recalculate_next_update_due_date(update_frequency, next_update_due, errors, context)
        else:
            errors[keys].append(_('Missing value'))
            raise StopOnError
    else:
        flattened_data[keys] = None


def validate_nature_of_change_data(keys, flattened_data, errors, context):
    '''
    Validate the nature of change data
    '''
    data = unflatten(flattened_data)
    res, index, key = keys
    resource = data.get(res, [])[index]

    next_update_due = data.get('next_update_due')
    update_frequency = data.get('update_frequency')
    nature_of_change = resource.get(key)

    if resource.get('id'):
        # Resource updated
        # Only validate the current resource being updated unless its coming from the API and is not a package_delete
        # The resource_data_updated value is set in  the 'before_update' IResource interface method 'check_resource_data'
        resource_data_updated = context.get('resource_data_updated', {})
        api_request = True if hasattr(request, 'params') and get_endpoint()[1] == 'action' and 'package_delete' not in request.path else False
        if api_request or resource_data_updated and resource_data_updated.get('id') == resource.get('id'):
            if api_request or resource_data_updated.get('data_updated', False) is True:
                # Resource data has been updated or the call is from the API so the nature_of_change validation is required
                if not nature_of_change or nature_of_change is missing:
                    errors[keys].append(_('Missing value'))
                    raise StopOnError

                h.update_last_modified(flattened_data, index, errors, context)
            # If nature_of_change is selected check value to see if the correct nature of change provided
            if nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
                h.recalculate_next_update_due_date(flattened_data, update_frequency, next_update_due, errors, context)
    else:
        # Resource created
        if update_frequency in h.get_update_frequencies():
            h.recalculate_next_update_due_date(flattened_data, update_frequency, next_update_due, errors, context)
        h.update_last_modified(flattened_data, index, errors, context)
        # Should not have a nature_of_change so remove it
        flattened_data.pop(keys, None)


def data_last_updated(keys, flattened_data, errors, context):
    '''
    Validate last data updated
    '''
    key, = keys
    data = unflatten(flattened_data)
    if not data.get('id'):
        # New dataset being created, there will be no resources so exit
        flattened_data[keys] = None
        return
    # Get package with 'package_show' because the validator doesn't have the resources when a dataset is updated
    package = get_action('package_show')(context, data)
    data_last_updated = get_validator('isodate')(package.get(key), context) if package.get(key) else None
    # Cycle through the resources to compare data_last_updated field with last_modified
    for resource in package.get('resources', []):
        last_modified = get_validator('isodate')(resource.get('last_modified') or resource.get('created'), context)
        if data_last_updated is None or last_modified > data_last_updated:
            data_last_updated = last_modified

    flattened_data[keys] = data_last_updated.isoformat() if isinstance(data_last_updated, dt.datetime) else None
