import sys

import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
from ckan.lib.cli import CkanCommand
from ckan.model.package import Package
from ckanapi import LocalCKAN
import ckan.logic as logic
ValidationError = logic.ValidationError

_and_ = sqlalchemy.and_


class DataQld(CkanCommand):
    """
    Data Qld custom commands

    Usage:
        paster data_qld

    """

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 9
    min_args = 0

    def __init__(self, name):
        super(DataQld, self).__init__(name)
        self.parser.add_option('-u', '--username_prefix',
                               dest='username_prefix',
                               help='Only demote usernames starting with this prefix',
                               type=str,
                               default='publisher-')

    def command(self):
        self._load_config()

        if len(self.args) != 1:
            self.parser.print_usage()
            sys.exit(1)

        cmd = self.args[0]
        if cmd == 'migrate_extras':
            self.migrate_extras()
        elif cmd == 'demote_publishers':
            self.demote_publishers()
        elif cmd == 'update_datasets':
            self.update_datasets()
        elif cmd == 'update_missing':
            self.update_missing_nature_of_change()
        else:
            self.parser.print_usage()

    def migrate_extras(self):
        """Migrates legacy field values that were added as free extras to datasets to their schema counterparts.
        """

        def _get_package_ids():
            session = model.Session
            packages = (
                session.query(
                    Package
                )
            )

            return [pkg.id for pkg in packages]

        def _update_package(package_id, security_classification,
                            data_driven_application, version, author_email,
                            notes, update_frequency, resources):
            # https://github.com/ckan/ckanext-scheming/issues/158
            destination = LocalCKAN()
            destination.action.package_patch(id=package_id, security_classification=security_classification,
                                             data_driven_application=data_driven_application,
                                             version=version,
                                             author_email=author_email,
                                             notes=notes,
                                             update_frequency=update_frequency,
                                             resources=resources)

        self._load_config()

        context = {'session': model.Session}

        # Step 1: Get all the package IDs.
        package_ids = _get_package_ids()

        for package_id in package_ids:
            # Set some defaults
            default_security_classification = "PUBLIC"
            default_data_driven_application = "NO"
            default_version = "1.0"
            default_author_email = "opendata@qld.gov.au"
            default_update_frequency = "annually"
            default_size = '1'  # 1 Byte
            resources = []

            pkg = toolkit.get_action('package_show')(context, {
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
                _update_package(package_id, security_classification, data_driven_application, version, author_email, notes, update_frequency, resources)
            except ValidationError as e:
                print('Package Failed: ', package_id, '\n', e.error_dict, )
                print('Package Payload: ', package_id, security_classification, data_driven_application, version, author_email, notes, update_frequency, resources)

        return 'SUCCESS'

    def demote_publishers(self):
        """Demotes any existing 'publisher-*' users from admin to editor in their respective organisations
        """
        self._load_config()

        def _get_organizations():
            return toolkit.get_action('organization_list')(data_dict={'all_fields': True, 'include_users': True})

        def _patch_organisation_users(org_id, users):
            toolkit.get_action('organization_patch')(data_dict={'id': org_id, 'users': users})

        username_prefix = self.options.username_prefix

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

    def update_datasets(self):
        '''
        Update datasets to trigger data_last_updated field
        '''
        context = {'session': model.Session}

        def _get_packages():

            return toolkit.get_action('package_list')(
                data_dict={
                    'all_fields': True,
                    'include_private': True,
                    'include_drafts': True
                }
            )

        def _update_package(pkg_dict):
            # Set some defaults
            toolkit.get_action('package_patch')(context, pkg_dict)

        self._load_config()

        updates = 0

        for package in _get_packages():
            try:
                package = toolkit.get_action('package_show')(context, {'id': package})
            except toolkit.ObjectNotFound:
                print('Package not found: %s' % package['id'])
                continue
            updates_required = False
            print('Processing package ID: %s | Name: %s' % (package['id'], package['name']))
            if package.get('data_last_updated', None) is None:
                print('- Setting data_last_updated for package %s' % package['id'])
                updates_required = True
                updates += 1
            else:
                print('- Nothing to update for package %s' % package['id'])
            if updates_required:
                _update_package(package)

        return "COMPLETED. Total updates %s\n" % updates

    def update_missing_nature_of_change(self):
        '''
        Update datasets to trigger data_last_updated field
        '''
        context = {'session': model.Session}

        def _get_packages():
            return toolkit.get_action('package_list')(
                data_dict={
                    'all_fields': True,
                    'include_private': True,
                    'include_drafts': True
                }
            )

        def _update_resource(res_dict):
            # Set some defaults
            toolkit.get_action('resource_patch')(context, res_dict)

        def _check_for_null_values(res, pkg_dict):
            print('- Setting nature_of_change for resource %s' % res['id'])
            res['nature_of_change'] = 'edit-resource-with-no-new-data'
            if res.get('resource_visibility', None):
                res['resource_visibility'] = 'Appropriate steps have been taken to minimise personal information re-identification risk prior to publishing'
            return res

        self._load_config()

        updates = 0

        for package in _get_packages():
            pkg_dict = toolkit.get_action('package_show')(context, {'id': package })
            for res in pkg_dict.get('resources', []):
                if res.get('nature_of_change') is None:
                    res = _check_for_null_values(res, pkg_dict)
                    _update_resource(res)

        return "COMPLETED. Total updates %s\n" % updates
