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

        if next_update_due.date() < dt.date.today():
            raise tk.ValidationError({key: [tk._("Date should be in future")]})

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

    res_id = resource.get('id', None)
    if not res_id:
        return
    nature_of_change = resource.get(key)
    file_upload = tk.request.params.get('upload', None)
    if isinstance(file_upload, uploader.ALLOWED_UPLOAD_TYPES):
        if not nature_of_change:
            raise tk.ValidationError({key: [tk._("Missing value")]})
    else:
        old_res = tk.get_action('resource_show')(context, {'id': res_id})
        if old_res.get('url') == resource.get('url'):
            return

    if not nature_of_change:
        raise tk.ValidationError({key: [tk._("Missing value")]})

    next_update_due = data.get('next_update_due')
    update_frequency = data.get('update_frequency')
    if nature_of_change == 'add-new-time-series' and update_frequency in h.get_update_frequencies():
        flattened_data[('next_update_due',)] = h.recalculate_next_update_due_date(update_frequency, next_update_due)
