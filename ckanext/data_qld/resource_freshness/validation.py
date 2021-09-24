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
            flattened_data[keys] = h.recalculate_next_update_due_date(update_frequency)
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
        # Only validate the current resource being updated unless its coming from the API
        # The resource_data_updated value is set in  the 'before_update' IResource interface method 'check_resource_data'
        resource_data_updated = context.get('resource_data_updated', {})
        api_request = True if hasattr(request, 'params') and get_endpoint()[1] == 'action' else False
        if api_request or resource_data_updated and resource_data_updated.get('id') == resource.get('id'):
            if api_request or resource_data_updated.get('data_updated', False) is True:
                # Resource data has been updated or the call is from the API so the nature_of_change validation is required
                if not nature_of_change or nature_of_change is missing:
                    errors[keys].append(_('Missing value'))
                    raise StopOnError

            # If nature_of_change is selected check value to see if the correct nature of change provided
            if nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
                h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)
    else:
        # Resource created
        h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)
        # Should not have a nature_of_change so remove it
        flattened_data.pop(keys, None)