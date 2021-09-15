# encoding: utf-8
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import datetime as dt

from ckanext.data_qld.resource_freshness.helpers import helpers as h

missing = tk.missing
StopOnError = tk.StopOnError


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
                errors[keys].append(tk._("Valid date in the future is required"))
        elif tk.get_endpoint()[1] == 'action':
            flattened_data[keys] = h.recalculate_next_update_due_date(update_frequency)
        else:
            errors[keys].append(tk._('Missing value'))
            raise StopOnError
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
        if resource_data_updated.get('id') == resource.get('id') and \
           resource_data_updated.get('data_updated', False) is True:
            # Resource data has updated so the nature_of_change validation is required
            if not nature_of_change or nature_of_change is missing:
                errors[keys].append(tk._('Missing value'))
            elif nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
                # Resource data has updated and the correct nature of change provided
                h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)
    else:
        # Resource created
        h.resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context)


def data_last_updated(key, flattened_data, errors, context):
    '''
    Validate last data updated
    '''
    key, = key
    data = df.unflatten(flattened_data)
    # Get package with 'pakcage_sho' because the validator doesnt have the all data required
    package = tk.get_action('package_show')(context, data)
    resources = package.get('resources')
    last_updated = tk.get_validator('isodate')(package.get('data_last_updated', ""), context)
    # Cycle through the resources to compare data_last_updated field with last_modified
    for resource in resources:
        last_modified = tk.get_validator('isodate')(resource.get('last_modified', ""), context)
        if last_modified is None:
            return
        if last_updated is None:
            last_updated = last_modified
        if last_modified > last_updated:
            last_updated = last_modified

    flattened_data[('data_last_updated', )] = tk.get_validator('convert_to_json_if_datetime')(last_updated, context)
