# encoding: utf-8
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import datetime as dt

from ckanext.data_qld.resource_freshness.helpers import helpers as h


def validate_next_update_due(keys, flattened_data, errors, context):
    '''
    Validate the next due date according the `update_frequency` input
    '''
    data = df.unflatten(flattened_data)
    key, = keys
    next_update_due = data.get(key)
    update_frequency = data.get('update_frequency')

    if update_frequency in h.get_update_frequencies():
        if next_update_due:
            next_update_due = tk.get_validator('isodate')(next_update_due, {})
            if next_update_due.date() <= dt.date.today():
                raise tk.ValidationError({key: [tk._("Valid date in the future is required")]})
        else:
            # Recalculate only if the request is coming from the API action
            if tk.get_endpoint()[1] == 'action':
                flattened_data[keys] = h.recalculate_next_update_due_date(update_frequency)
            else:
                raise tk.ValidationError({key: [tk._("Missing value")]})
    else:
        flattened_data[keys] = None


def validate_nature_of_change_data(keys, flattened_data, errors, context):
    '''
    Validate the nature of change data
    '''
    data = df.unflatten(flattened_data)
    res, index, key = keys
    resource = data.get(res, [])[index]

    next_update_due = data.get('next_update_due')
    update_frequency = data.get('update_frequency')
    nature_of_change = resource.get(key)

    if resource.get('id'):
        # Resource updated
        # # The resource_data_updated value is set in  the 'before_update' IResource interface method 'check_resource_data'
        resource_data_updated = context.get('resource_data_updated', {})
        if (resource_data_updated.get('id') == resource.get('id') and
                resource_data_updated.get('data_updated', False) == True):
            # Resource data has updated so the nature_of_change validation is required
            if not nature_of_change:
                raise tk.ValidationError({key: [tk._("Missing value")]})
            elif nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
                # Resource data has updated and the correct nature of change provided
                h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)
    else:
        # Resource created
        h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)
