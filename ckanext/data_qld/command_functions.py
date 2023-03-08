# encoding: utf-8

import logging

from ckantoolkit import get_action, ValidationError, h, get_validator

from ckan import model

from ckanext.data_qld.resource_freshness.helpers import helpers as resource_freshness_helpers

log = logging.getLogger(__name__)


def migrate_extras(package_ids):
    """

    :return:
    """
    context = {'ignore_auth': True}
    package_ids = [pkg['id']
                   for pkg in get_action('package_list')(context=context)]

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
            print('Package Payload: ', package_id, security_classification, data_driven_application,
                  version, author_email, notes, update_frequency, resources)

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
        print('Processing organisation ID: %s | Name: %s' %
              (org['id'], org['name']))
        if users:
            for user in org['users']:
                if user['name'].startswith(username_prefix) and user['capacity'] == 'admin':
                    print('- Setting capacity for user %s to "editor" in organisation %s' %
                          (user['name'], org['name']))
                    user['capacity'] = 'editor'
                    updates_required = True
                    updates += 1
            if updates_required:
                print('- Updating user capacities for organisation %s' %
                      org['name'])
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


def update_missing_values():
    '''
    Update datasets to set default values for metadata
    '''
    context = {'session': model.Session}
    site_user = get_action('get_site_user')({'ignore_auth': True}, {})
    context['user'] = site_user['name']

    def _get_packages():
        return model.Session.query(model.Package).filter(model.Package.state == 'active').all()

    def _update_package(package_dict):
        # Set some defaults
        try:
            print('Updating package {0}'.format(package_dict['id']))
            get_action('package_patch')(context, package_dict)
            return True
        except Exception as ex:
            print('Package exception: %s' % ex)
            return False

    def _update_resource(res_dict):
        # Set some defaults
        try:
            print('Updating resource {0}'.format(res_dict['id']))
            get_action('resource_patch')(context, res_dict)
            return True
        except Exception as ex:
            print('Resource exception: %s' % ex)
            return False

    def _populate_package_values(package):
        package_patch = {"id": package.get('id')}

        # All custom metadata will be in the extras
        extras = package.get('extras', {})

        if not extras.get('de_identified_data'):
            package_patch['de_identified_data'] = 'NO'

        if not extras.get('data_last_updated'):
            # Set empty value to trigger package_patch which will call the validator data_qld_data_last_updated to set value from resources
            package_patch['data_last_updated'] = ''

        return package_patch

    def _populate_resource_values(res, package_patch):
        resource_patch = {"id": res.get('id')}

        if not res.get('nature_of_change'):
            resource_patch['nature_of_change'] = 'edit-resource-with-no-new-data'

        # Migrate the existing field `resource_visibility` and map to two new fields `resource_visible` `governance_acknowledgement`
        if not res.get('resource_visibility'):
            resource_patch['resource_visible'] = 'TRUE'
            resource_patch['governance_acknowledgement'] = 'NO'
        elif res['resource_visibility'] == 'Resource visible and re-identification risk governance acknowledgement not required':
            resource_patch['resource_visible'] = 'TRUE'
            resource_patch['governance_acknowledgement'] = 'NO'
        elif res['resource_visibility'] == 'Appropriate steps have been taken to minimise personal information re-identification risk prior to publishing':
            resource_patch['resource_visible'] = 'TRUE'
            resource_patch['governance_acknowledgement'] = 'YES'
        elif res['resource_visibility'] == 'Resource NOT visible/Pending acknowledgement':
            resource_patch['resource_visible'] = 'FALSE'
            resource_patch['governance_acknowledgement'] = 'NO'

        if not res.get('last_modified'):
            h.populate_revision(res)
            last_modified = res.get('revision_timestamp') or res.get('created')
            resource_patch['last_modified'] = get_validator(
                'convert_to_json_if_datetime')(last_modified, context)
            # We need to trigger a package_patch to trigger the data_qld_data_last_updated validator to re-calculate data_last_updated
            package_patch['data_last_updated'] = ''

        return (resource_patch, package_patch)

    packages_total = 0
    package_updates = 0
    package_errors = 0
    resources_total = 0
    resource_updates = 0
    resource_errors = 0
    packages = _get_packages()
    for package in packages:
        packages_total += 1
        package_patch = _populate_package_values(package.as_dict())
        # Update resource values first so the resource last_modified values can be used to calculate dataset data_last_updated
        for resource in package.resources:
            resources_total += 1
            resource_patch, package_patch = _populate_resource_values(
                resource.as_dict(), package_patch)
            if len(resource_patch.items()) > 1:
                result = _update_resource(resource_patch)
                if result is True:
                    resource_updates += 1
                else:
                    resource_errors += 1

        if len(package_patch.items()) > 1:
            result = _update_package(package_patch)
            if result is True:
                package_updates += 1
            else:
                package_errors += 1

    print("Updated packages. Total:{0}. Updates:{1}. Errors:{2}".format(
        packages_total, package_updates, package_errors))
    print("Updated resources. Total:{0}. Updates:{1}. Errors:{2}".format(
        resources_total, resource_updates, resource_errors))

    return "COMPLETED update_missing_values"
