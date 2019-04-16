# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import logging

def data_driven_application(data_driven_application):
    '''Returns True if data_driven_application value equals yes
        Case insensitive 

    :rtype: boolean

    '''
    if data_driven_application and data_driven_application.lower() == 'yes':
        return True
    else:
        return False


def resource_data_driven_application(resource_id):
    '''Returns True if the resource for resource_id parent dataset data_driven_application value equals yes
        Case insensitive 

    :rtype: boolean

    '''
    try:
        resource = toolkit.get_action('resource_show')(
            data_dict={'id': resource_id})
    except toolkit.ObjectNotFound:
        return False

    return dataset_data_driven_application(resource['package_id'])


def dataset_data_driven_application(dataset_id):
    '''Returns True if the dataset for dataset_id data_driven_application value equals yes
        Case insensitive 

    :rtype: boolean

    '''
    try:
        package = toolkit.get_action('package_show')(
            data_dict={'id': dataset_id})
    except toolkit.ObjectNotFound:
        return False

    return data_driven_application(package.get('data_driven_application',''))


class DataQldPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld')

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_data_driven_application': data_driven_application,
                'data_qld_resource_data_driven_application': resource_data_driven_application}

    # IPackageController
    def set_maintainer_from_author(self, entity):
        entity.maintainer = entity.author
        entity.maintainer_email = entity.author_email

    def create(self, entity):
        self.set_maintainer_from_author(entity)

    def edit(self, entity):
        self.set_maintainer_from_author(entity)
