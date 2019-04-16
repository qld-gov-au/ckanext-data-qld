import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
import re
import requests

from ckan.model.resource import Resource
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
        package_ids = ['fireworks']

        return package_ids


    def update_package_security(self, package_id, security_classification):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id, security_classification=security_classification)

    def update_package_application(self, package_id, application):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id, data_driven_application=application)

    def command(self):
        '''

        :return:
        '''
        self._load_config()


        context = {'session': model.Session}

        # Step 1: Get all the package IDs
        package_ids = self.get_package_ids()

        for package_id in package_ids:
            pkg = toolkit.get_action('package_show')(context, {
                'id': package_id
            })

            # Go through the packages and check for presence of 'Security classification'
            # and 'Used in data-driven application' extras
            if pkg['extras']:
                for extra in pkg['extras']:
                    if extra['key'] == 'Security classification':
                        print 'Found ' + extra['key'] + ' | value: ' + extra['value']
                        self.update_package_security(package_id, extra['value'])
                    elif extra['key'] in ['Used in data-driven application']:
                        print 'Found ' + extra['key'] + ' | value: ' + extra['value']
                        self.update_package_application(package_id, extra['value'])

        return 'SUCCESS'
