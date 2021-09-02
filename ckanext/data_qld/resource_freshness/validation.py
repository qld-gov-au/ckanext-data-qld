# encoding: utf-8
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import datetime as dt
import ckan.lib.uploader as uploader

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
        if not next_update_due:
            raise tk.ValidationError({key: [tk._("Missing value")]})

        next_update_due = tk.get_validator('isodate')(next_update_due, {})
        if next_update_due.date() <= dt.date.today():
            raise tk.ValidationError({key: [tk._("Valid date in the future is required")]})

        # Recalculate only IF the request is API call
        if tk.get_endpoint()[1] == 'action':
            flattened_data[keys] = h.recalculate_next_update_due_date(update_frequency, next_update_due)


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
    res_id = resource.get('id', None)

    if not res_id:
        # New resource created, recalculate next_update_due date
        flattened_data[('next_update_due',)] = h.recalculate_next_update_due_date(update_frequency)
        tk.get_validator('convert_to_extras')(('next_update_due', ), flattened_data, errors, context)
        return

    # Compare old resource url with current url to find out if the resource data has changed
    # url value can be updated from either a new file uploaded which stores the filename in URL or the url link updated
    old_res = tk.get_action('resource_show')(context, {'id': res_id})
    if resource.get('url', '').endswith(old_res.get('url', '')):
        # URL has not been updated so no nature_of_change validation required
        return

    if not nature_of_change:
        raise tk.ValidationError({key: [tk._("Missing value")]})

    if nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
        # Resource data has been updated and the correct nature of change provided, recalculate next_update_due date
        flattened_data[('next_update_due',)] = h.recalculate_next_update_due_date(update_frequency, next_update_due)
        tk.get_validator('convert_to_extras')(('next_update_due', ), flattened_data, errors, context)
