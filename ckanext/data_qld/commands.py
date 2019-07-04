import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
from ckan.lib.cli import CkanCommand
from ckan.model.package import Package
from ckanapi import LocalCKAN

_and_ = sqlalchemy.and_


class MigrateExtras(CkanCommand):
    """Migrates legacy field values that were added as free extras to datasets to their schema counterparts.
    """

    summary = __doc__.split('\n')[0]

    def __init__(self, name):

        super(MigrateExtras, self).__init__(name)

    def get_package_ids(self):
        session = model.Session
        package_ids = []

        packages = (
            session.query(
                Package
            )
        )

        for pkg in packages:
            package_ids.append(pkg.id)

        return package_ids

    def update_package(self, package_id, security_classification, data_driven_application, version, author_email, notes, update_frequency, resources):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id,
                                         security_classification=security_classification,
                                         data_driven_application=data_driven_application,
                                         version=version,
                                         author_email=author_email,
                                         notes=notes,
                                         update_frequency=update_frequency,
                                         resources=resources)

    def command(self):
        """

        :return:
        """
        self._load_config()

        context = {'session': model.Session}

        # Step 1: Get all the package IDs.
        package_ids = self.get_package_ids()

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
                        "description": description
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

            self.update_package(package_id, security_classification, data_driven_application, version, author_email, notes, update_frequency, resources)

        return 'SUCCESS'


class DemotePublishers(CkanCommand):
    """Demotes any existing 'publisher-*' users from admin to editor in their respective organisations
    """

    summary = __doc__.split('\n')[0]

    def __init__(self, name):

        super(DemotePublishers, self).__init__(name)
        self.parser.add_option('-u', '--username_prefix', dest='username_prefix', help='Only demote usernames starting with this prefix', type=str, default='publisher-')

    def get_organizations(self):
        return toolkit.get_action('organization_list')(data_dict={'all_fields': True, 'include_users': True})

    def patch_organisation_users(self, org_id, users):
        toolkit.get_action('organization_patch')(data_dict={'id': org_id, 'users': users})

    def command(self):
        """

        :return:
        """
        self._load_config()

        username_prefix = self.options.username_prefix

        updates = 0

        for org in self.get_organizations():
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
                    self.patch_organisation_users(org['id'], users)
                else:
                    print('- Nothing to update for organisation %s' % org['name'])

        print('- - - - - - - - - - - - - - - - - - - - - - - - -')

        return "COMPLETED. Total updates %s\n" % updates
