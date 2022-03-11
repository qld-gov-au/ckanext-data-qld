# encoding: utf-8

import logging

from ckantoolkit import get_action, ValidationError

from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers

log = logging.getLogger(__name__)


def migrate_extras(package_ids):
    """

    :return:
    """
    context = {'ignore_auth': True}
    package_ids = [pkg['id'] for pkg in get_action('package_list')(context=context)]

    package_patch = get_action('package_patch')
    # Step 1: Get all the package IDs.
    for package_id in package_ids:
        # Set some defaults
        default_security_classification = "PUBLIC"
        default_data_driven_application = "NO"
        default_version = "1.0"
        default_author_email = "opendata@qld.gov.au"
        default_update_frequency = "annually"
        default_size = '1'  # 1 Byte
        resources = []

        pkg = get_action('package_show')(context, {
            'id': package_id
        })

        if pkg['resources']:
            size = default_size

            for resource in pkg['resources']:
                if 'size' in resource:
                    size = resource['size'] if resource['size'] is not None and resource[
                        'size'] != '0 bytes' else default_size

                if 'name' in resource:
                    name = resource['name']

                if 'description' in resource:
                    description = resource['description'] or name

                update_resource = {
                    "id": resource['id'],
                    "size": size,
                    "name": name,
                    "description": description,
                    "url": resource['url']
                }
                resources.append(update_resource)

        # Go through the packages and check for presence of 'Security classification'
        # and 'Used in data-driven application' extras
        security_classification = default_security_classification
        data_driven_application = default_data_driven_application
        version = default_version
        author_email = default_author_email
        update_frequency = default_update_frequency

        if pkg.get('extras', None):

            for extra in pkg['extras']:
                if extra['key'] == 'Security classification':
                    security_classification = extra['value'] or default_security_classification
                elif extra['key'] in ['Used in data-driven application']:
                    data_driven_application = extra['value'] or default_data_driven_application

        if 'version' in pkg:
            version = pkg['version'] or default_version

        if 'author_email' in pkg:
            author_email = pkg['author_email'] or default_author_email

        if 'notes' in pkg:
            notes = pkg['notes'] or pkg['title']

        if 'update_frequency' in pkg:
            update_frequency = pkg['update_frequency'] or default_update_frequency

        try:
            package_patch(
                context=context,
                data_dict={
                    'id': package_id,
                    'security_classification': security_classification,
                    'data_driven_application': data_driven_application,
                    'version': version,
                    'author_email': author_email,
                    'notes': notes,
                    'update_frequency': update_frequency,
                    'resources': resources
                })
        except ValidationError as e:
            print('Package Failed: ', package_id, '\n', e.error_dict, )
            print('Package Payload: ', package_id, security_classification, data_driven_application, version, author_email, notes, update_frequency, resources)

    return 'SUCCESS'


def _get_organizations():
    return get_action('organization_list')(data_dict={'all_fields': True, 'include_users': True})


def _patch_organisation_users(org_id, users):
    return get_action('organization_patch')(data_dict={'id': org_id, 'users': users})


def demote_publishers(username_prefix):
    """

    :return:
    """
    updates = 0

    for org in _get_organizations():
        print('- - - - - - - - - - - - - - - - - - - - - - - - -')
        updates_required = False
        users = org.get('users', [])
        print('Processing organisation ID: %s | Name: %s' % (org['id'], org['name']))
        if users:
            for user in org['users']:
                if user['name'].startswith(username_prefix) and user['capacity'] == 'admin':
                    print('- Setting capacity for user %s to "editor" in organisation %s' % (user['name'], org['name']))
                    user['capacity'] = 'editor'
                    updates_required = True
                    updates += 1
            if updates_required:
                print('- Updating user capacities for organisation %s' % org['name'])
                _patch_organisation_users(org['id'], users)
            else:
                print('- Nothing to update for organisation %s' % org['name'])

    print('- - - - - - - - - - - - - - - - - - - - - - - - -')

    return "COMPLETED. Total updates %s\n" % updates


def send_email_dataset_due_to_publishing_notification():
    # Need to do CKAN imports and logger after load config
    log.info('Started command SendEmailDatasetDueToPublishingNotification')
    resource_freshness_helpers.process_email_notification_for_dataset_due_to_publishing()
    log.info('Finished command SendEmailDatasetDueToPublishingNotification')


def send_email_dataset_overdue_notification():
    # Need to do CKAN imports and logger after load config
    log.info('Started command SendEmailDatasetOverdueNotification')
    resource_freshness_helpers.process_email_notification_for_dataset_overdue()
    log.info('Finished command SendEmailDatasetOverdueNotification')
