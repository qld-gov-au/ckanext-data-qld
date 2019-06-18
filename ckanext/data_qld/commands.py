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

    def update_package(self, package_id, security_classification, data_driven_application, version, author_email, notes,
                       resources):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id,
                                         security_classification=security_classification,
                                         data_driven_application=data_driven_application,
                                         version=version,
                                         author_email=author_email,
                                         notes=notes,
                                         resources=resources)

    def try_parsing_date(self, text, resource_id, default_expiration_date):
        for fmt in (
                '%d/%m/%Y', '%d/%m/%y', '%d.%m.%Y', '%d.%m.%y', '%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d', '%y-%m-%d', '%Y/%m/%d',
                '%y/%m/%d', '%d-%B-%Y', '%d-%B-%y', '%d %B %Y', '%d %B %y'):
            try:
                parsed_date = datetime.strptime(text.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
        print("try_parsing_date failed: {0} for ResourceId: {1} ".format(str(text), str(resource_id)))
        return default_expiration_date

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
            default_expiration_date = "2020-06-30"
            default_size = '1'  # 1 Byte
            resources = []

            pkg = toolkit.get_action('package_show')(context, {
                'id': package_id
            })

            # Update the 'Expiration date' field in Resources.
            if pkg['resources']:
                size = default_size

                for resource in pkg['resources']:
                    if 'Expiration date' in resource:
                        if resource['Expiration date']:
                            expiration_date = self.try_parsing_date(resource['Expiration date'], resource['id'],
                                                                    default_expiration_date)
                        else:
                            expiration_date = default_expiration_date
                    elif 'ExpirationDate' in resource:
                        if resource['ExpirationDate']:
                            expiration_date = self.try_parsing_date(resource['ExpirationDate'], resource['id'],
                                                                    default_expiration_date)
                        else:
                            expiration_date = default_expiration_date
                    elif 'expiration_date' in resource:
                        if resource['expiration_date']:
                            expiration_date = self.try_parsing_date(resource['expiration_date'], resource['id'],
                                                                    default_expiration_date)
                        else:
                            expiration_date = default_expiration_date
                    elif 'expiration-date' in resource:
                        if resource['expiration-date']:
                            expiration_date = self.try_parsing_date(resource['expiration-date'], resource['id'],
                                                                    default_expiration_date)
                        else:
                            expiration_date = default_expiration_date

                    else:
                        expiration_date = default_expiration_date

                    if 'size' in resource:
                        size = resource['size'] if resource['size'] is not None and resource[
                            'size'] != '0 bytes' else default_size

                    if 'name' in resource:
                        name = resource['name']

                    if 'description' in resource:
                        description = resource['description'] or name

                    update_resource = {
                        "id": resource['id'],
                        "expiration_date": expiration_date,
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

            self.update_package(package_id, security_classification, data_driven_application, version, author_email,
                                notes, resources)

        return 'SUCCESS'
