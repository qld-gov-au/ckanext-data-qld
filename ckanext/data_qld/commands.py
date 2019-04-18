import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
import re
import requests

from ckan.model.package import Package
from ckan.model.package_extra import PackageExtra

from ckan.lib.cli import CkanCommand
from pprint import pprint
from ckanapi import LocalCKAN, ValidationError

_and_ = sqlalchemy.and_


class MigrateExtras(CkanCommand):
    '''Migrates
    '''

    summary = __doc__.split('\n')[0]

    def __init__(self,name):

        super(MigrateExtras,self).__init__(name)

    def get_package_ids(self):
        # @Todo: Load all packages
        # package_ids = ['gifts-and-benefits-register-department-of-aboriginal-and-torres-strait-islander-partnerships']
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

    def update_package(self, package_id, security_classification, data_driven_application):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id,
                                         security_classification=security_classification,
                                         data_driven_application=data_driven_application)

    def update_resource(self, resource_id, expiration_date):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.resource_patch(id=resource_id,
                                         expiration_date=expiration_date)

    def command(self):
        '''

        :return:
        '''
        self._load_config()

        context = {'session': model.Session}

        # Step 1: Get all the package IDs
        package_ids = self.get_package_ids()

        for package_id in package_ids:

            print(package_id)

            # Set some defaults
            security_classification = "PUBLIC"
            data_driven_application = "NO"

            pkg = toolkit.get_action('package_show')(context, {
                'id': package_id
            })

            #pprint(pkg)

            # Go through the packages and check for presence of 'Security classification'
            # and 'Used in data-driven application' extras
            if pkg.get('extras', None):
                for extra in pkg['extras']:
                    if extra['key'] == 'Security classification':
                        print 'Found ' + extra['key'] + ' | value: ' + extra['value']
                        security_classification = extra['value']
                    elif extra['key'] in ['Used in data-driven application']:
                        print 'Found ' + extra['key'] + ' | value: ' + extra['value']
                        data_driven_application = extra['value']

                    self.update_package(package_id, security_classification, data_driven_application)

            # @Todo: Need to handle the date conversion
            # Update the 'Expiration date' field in Resources
            # if pkg['resources']:
            #     for resource in pkg['resources']:
            #         if 'Expiration date' in resource:
            #             print 'This resource has Expiration date: '
            #             pprint(resource['Expiration date'])
            #             self.update_resource(resource['id'], resource['Expiration date'])

        return 'SUCCESS'
