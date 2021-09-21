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
    "half-yearly": 182,
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


def recalculate_next_update_due_date(flattened_data, update_frequency, next_update_due, errors, context):
    days = get_update_frequencies().get(update_frequency, 0)
    # Recalculate the next_update_due if its not none
    if next_update_due is not None:
        next_update_due = get_validator('isodate')(next_update_due, {})
        due_date = next_update_due.date() + dt.timedelta(days=days)
    else:
        # Recalculate the UpdateDue date if its None
        due_date = dt.datetime.utcnow().date() + dt.timedelta(days=days)

    flattened_data[('next_update_due',)] = due_date.isoformat()
    get_validator('convert_to_extras')(('next_update_due',), flattened_data, errors, context)


def update_last_modified(flattened_data, index, errors, context):
    now = dt.datetime.utcnow()
    flattened_data[('resources', index, 'last_modified')] = now
    flattened_data[('data_last_updated', )] = now.isoformat()
    get_validator('convert_to_extras')(('data_last_updated',), flattened_data, errors, context)


def check_resource_data(current_resource, updated_resource, context):
    # If there are validation errors we cannot determine if the resource data was updated on the previous submit
    # Need to store this state in the form as a hidden field so we can retrieve the value here
    data_updated = updated_resource.pop('resource_data_updated') == "true" if 'resource_data_updated' in updated_resource else False

    if not data_updated:
        # If the clear_upload field is set to true it means the user clicked on the clear button to update the url
        data_updated = updated_resource.get('clear_upload') == "true"

    if not data_updated:
        # If there is a file upload object of ALLOWED_UPLOAD_TYPES a new file is being uploaded
        data_updated = isinstance(updated_resource.get('upload'), uploader.ALLOWED_UPLOAD_TYPES)

    if not data_updated:
        # Compare urls
        updated_resource_url = updated_resource.get('url', '')
        if current_resource.get('url_type', '') == 'upload':
            # Strip the full url for resources of type 'upload' to get filename for compare
            current_resource_url = current_resource.get('url', '').rsplit('/')[-1]
        else:
            current_resource_url = current_resource.get('url', '')
        # Compare old resource url with current url to find out if the resource data has changed
        data_updated = current_resource_url != updated_resource_url

    # The context['resource_data_updated'] value will be used in the validator 'validate_nature_of_change_data'
    context['resource_data_updated'] = {
        'id': updated_resource.get('id'),
        'data_updated': data_updated
    }

    # This will be used in the 'upload.html' to inject hidden fields if there are any validation errors
    # We need to know if the data was updated to fix an issue with CKAN losing this state with validation errors
    tk.g.resource_data_updated = data_updated


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
