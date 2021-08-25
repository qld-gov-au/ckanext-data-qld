# encoding: utf-8

import pdb
from sqlalchemy.sql.expression import update
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.lib.uploader as uploader
import ckan.lib.navl.dictization_functions as df
import ckan.model as model
import logging
import datetime

from ckanext.data_qld.currency.helpers import helpers as h

UPDATE_FREQUENCY = ['annually', 'semiannually', 'quarterly', 'monthly']


def validate_next_due_date(keys, flattened_data, errors, context):
    '''
    Validate the next due date according the `update_frequency` input
    '''
    data = df.unflatten(flattened_data)
    key, = keys

    if not data[key] and data['update_frequency'] in UPDATE_FREQUENCY:
        raise tk.ValidationError({key: [tk._("Missing value")]})
