import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
from ckan.lib.cli import CkanCommand
from ckan.model.package import Package
from ckanapi import LocalCKAN
from datetime import datetime

_and_ = sqlalchemy.and_


class MigrateExtras(CkanCommand):
    """Migrates
    """

    summary = __doc__.split('\n')[0]

    def __init__(self, name):

        super(MigrateExtras, self).__init__(name)

    def get_package_ids(self):
        # @Todo: Load all packages
        # package_ids = ['f0742c45-995d-4299-9d79-f0b777e2d0eb']
        # return package_ids
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

            # Update the 'Expiration date' field in Resources.
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
