# encoding: utf-8

from sqlalchemy.sql.expression import update
import ckan.plugins.toolkit as tk
import ckan.lib.navl.dictization_functions as df
import logging
import datetime as dt

from ckanext.data_qld.currency.helpers import helpers as h


def validate_next_due_date(keys, flattened_data, errors, context):
    '''
    Validate the next due date according the `update_frequency` input
    '''
    data = df.unflatten(flattened_data)
    key, = keys
    if data['update_frequency'] in h.get_update_frequencies():
        if not data[key]:
            raise tk.ValidationError({key: [tk._("Missing value")]})

        if dt.datetime.strptime(data[key], '%Y-%m-%d').date() < dt.date.today():
            raise tk.ValidationError({key: [tk._("Date should be in future")]}) 

        flattened_data[keys] = h.recalculate_due_date(data['update_frequency'], data[key])


def validate_nature_of_change_data(keys, flattened_data, errors, context):
    '''
    Validate the nature of change data
    '''
    # import pdb; pdb.set_trace()
    data = df.unflatten(flattened_data)
    res, _, key = keys
    for resource in data[res]:
        if not resource[key]:
            raise tk.ValidationError({key: [tk._("Missing value")]})
        if resource[key] == 'add-new-time-series' and data['update_frequency'] in h.get_update_frequencies():
            flattened_data[('next_update_due',)] = h.recalculate_due_date(data['update_frequency'], data['next_update_due'])