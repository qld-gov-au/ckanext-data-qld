import datetime as dt
import json
import logging
import ckan.plugins.toolkit as tk
import ckan.lib.uploader as uploader

from ckan.lib.base import config
from ckanext.data_qld import helpers as h

log = logging.getLogger(__name__)
get_validator = tk.get_validator

update_frequencies = {
    "monthly": 30,
    "quarterly": 91,
    "semiannually": 182,
    "annually": 365
}


def get_update_frequencies():
    try:
        return json.loads(update_frequencies_from_config())
    except ValueError:
        log.warning('Unable to load update frequencies from config')
        return update_frequencies


def update_frequencies_from_config():
    return config.get('ckanext.resource_freshness.update_frequencies', json.dumps(update_frequencies))


def recalculate_next_update_due_date(update_frequency, next_update_due=None):
    days = get_update_frequencies().get(update_frequency, 0)
    # Recalcualte the next_update_due if its not none
    if next_update_due is not None:
        next_update_due = get_validator('isodate')(next_update_due, {})
        due_date = next_update_due.date() + dt.timedelta(days=days)
    else:
        # Recalculate the UpdateDue date if its None
        due_date = dt.datetime.utcnow().date() + dt.timedelta(days=days)

    return get_validator('convert_to_json_if_date')(due_date, {})


def resource_data_updated(flattened_data, update_frequency, next_update_due, index, errors, context):
    flattened_data[('next_update_due',)] = recalculate_next_update_due_date(update_frequency, next_update_due)
    get_validator('convert_to_extras')(('next_update_due',), flattened_data, errors, context)
    flattened_data[('resources', index, 'last_modified')] = dt.datetime.utcnow()


def check_resource_data(current_resource, updated_resource, context):
    data_updated = False
    # If there is a file upload object of ALLOWED_UPLOAD_TYPES a new file is being uploaded
    data_updated = isinstance(updated_resource.get(u'upload'), uploader.ALLOWED_UPLOAD_TYPES)
    if not data_updated:
        current_resource_url = ''
        updated_resource_url = ''
        if current_resource.get('url_type') == 'upload':
            # Strip the full url for resources of type 'upload' to get filename for compare
            current_resource_url = current_resource.get('url', '').rsplit('/')[-1]
            updated_resource_url = updated_resource.get('url', '').rsplit('/')[-1]
        else:
            current_resource_url = current_resource.get('url', '')
            updated_resource_url = updated_resource.get('url', '')
        # Compare old resource url with current url to find out if the resource data has changed
        data_updated = current_resource_url != updated_resource_url
    # The context['resource_data_updated'] value will be used in the validator 'validate_nature_of_change_data'
    context['resource_data_updated'] = {
        'id': updated_resource.get('id'),
        'data_updated': data_updated
    }


def process_next_update_due(data_dict):
    if not h.user_has_admin_access(True):
        if 'next_update_due' in data_dict:
            del data_dict['next_update_due']
        for res in data_dict.get('resources', []):
            if 'nature_of_change' in res:
                del res['nature_of_change']


def process_nature_of_change(resource_dict):
    if 'nature_of_change' in resource_dict:
        del resource_dict['nature_of_change']
