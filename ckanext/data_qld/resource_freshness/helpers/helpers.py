import datetime as dt
import json
import logging
import ckan.plugins.toolkit as tk
import ckan.lib.base as base
import ckan.lib.mailer as mailer
import ckan.lib.uploader as uploader

from ckanext.data_qld import helpers as data_qld_helpers
from datetime import datetime
from itertools import groupby

log = logging.getLogger(__name__)
get_validator = tk.get_validator
config = tk.config
h = tk.h

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


def recalculate_next_update_due_date(flattened_data, update_frequency, errors, context):
    days = get_update_frequencies().get(update_frequency, 0)
    # Recalculate the next_update_due always against today's date
    today = dt.datetime.now(h.get_display_timezone())
    due_date = today + dt.timedelta(days=days)

    flattened_data[('next_update_due',)] = due_date.date().isoformat()
    get_validator('convert_to_extras')(('next_update_due',), flattened_data, errors, context)


def update_last_modified(flattened_data, index, errors, context):
    now = dt.datetime.utcnow()
    flattened_data[('resources', index, 'last_modified')] = now
    flattened_data[('data_last_updated', )] = now.isoformat()
    get_validator('convert_to_extras')(('data_last_updated',), flattened_data, errors, context)


def check_resource_data(current_resource, updated_resource, context):
    # If there are validation errors we cannot determine if the resource data was updated on the previous submit
    # Need to store this state in the form as a hidden field so we can retrieve the value here
    data_updated = updated_resource.get('resource_data_updated') == "true"

    # Remove hidden field values from form so they do not get saved as extras
    updated_resource.pop('resource_data_updated', None)
    updated_resource.pop('update_frequency_days', None)
    updated_resource.pop('update_frequency', None)

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
    if not data_qld_helpers.user_has_admin_access(True):
        if 'next_update_due' in data_dict:
            del data_dict['next_update_due']
        for res in data_dict.get('resources', []):
            if 'nature_of_change' in res:
                del res['nature_of_change']


def process_nature_of_change(resource_dict):
    if 'nature_of_change' in resource_dict:
        del resource_dict['nature_of_change']


def group_dataset_by_contact_email(datasets):
    def key_func(dt):
        return dt['author_email']

    datasets_by_contact = []
    for key, value in groupby(datasets, key_func):
        datasets_by_contact.append({'email': key, 'datasets': list(value)})

    return datasets_by_contact


def send_email_dataset_notification(datasets_by_contacts, action_type):
    for contact in datasets_by_contacts:
        try:
            datasets = []
            for contact_dataset in contact.get('datasets', {}):
                date = datetime.strptime(contact_dataset.get('next_update_due'), '%Y-%m-%d')

                datasets.append({
                    'url': tk.h.url_for('dataset_read', id=contact_dataset.get('name'), _external=True),
                    'next_due_date': date.strftime('%d/%m/%Y')
                })

            extra_vars = {'datasets': datasets}
            subject = base.render_jinja2('emails/subjects/{0}.txt'.format(action_type), extra_vars)
            body = base.render_jinja2('emails/bodies/{0}.txt'.format(action_type), extra_vars)

            site_title = 'Data | Queensland Government'
            site_url = config.get('ckan.site_url')
            tk.enqueue_job(mailer._mail_recipient, [contact.get('email'), contact.get('email'), site_title, site_url, subject, body], title=action_type)
        except Exception:
            log.error("Error sending {0} notification to {1}".format(action_type, contact.get('email')))


def process_email_notification_for_dataset_due_to_publishing():
    results = tk.get_action('data_qld_get_dataset_due_to_publishing')({}, {}).get('results', [])
    if results:
        datasets_by_contacts = group_dataset_by_contact_email(results)
        send_email_dataset_notification(datasets_by_contacts, 'send_email_dataset_due_to_publishing_notification')


def process_email_notification_for_dataset_overdue():
    results = tk.get_action('data_qld_get_dataset_overdue')({}, {}).get('results', [])
    if results:
        datasets_by_contacts = group_dataset_by_contact_email(results)
        send_email_dataset_notification(datasets_by_contacts, 'send_email_dataset_overdue_notification')
