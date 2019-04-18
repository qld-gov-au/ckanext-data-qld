# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.plugins.toolkit import Invalid
import re
import ckan.lib.formatters as formatters


def data_driven_application(data_driven_application):
    '''Returns True if data_driven_application value equals yes
        Case insensitive 

    :rtype: boolean

    '''
    if data_driven_application and data_driven_application.lower() == 'yes':
        return True
    else:
        return False


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

    return data_driven_application(package.get('data_driven_application', ''))


def file_size_converter(value, context):
    '''Returns the converted size into bytes 

    :rtype: int

    '''
    value = str(value)
    # remove whitespaces
    value = re.sub(' ', '', value)
    # remove commas
    value = re.sub(',', '', value)
    value = value.upper()

    # If the size is not all digits then get size converted into bytes
    if re.search(r'^\d+$', value) is None:
        value = file_size_bytes(value)

    return value


def file_size_bytes(value):
    '''Returns the converted size into bytes 
        size types TERABYTES, GIGABYTES, MEGABYTES, KILOBYTES
    :rtype: int

    '''
    if re.search(r'^\d*\.?\d+[A-Za-z]*$', value) is not None:
        size_type = re.search(r'[A-Za-z]+', value)
        size_number = re.search(r'\d*\.?\d*', value)

        if size_type is None or size_number is None:
            raise Invalid('Must be a valid filesize format (e.g. 123, 1.2KB, 2.5MB)')
        else:
            size_type = size_type.group()
            size_number = int(size_number.group())

        if size_type == 'TB' or size_type == 'T' or size_type == 'TERABYTES' or size_type == 'TBS' or size_type == 'TIB':
            fileMultiplier = 1099511627776
        elif size_type == 'GB' or size_type == 'G' or size_type == 'GIGABYTES' or size_type == 'GIG' or size_type == 'GBS' or size_type == 'GIB':
            fileMultiplier = 1073741824
        elif size_type == 'MB' or size_type == 'M' or size_type == 'MEGABYTES' or size_type == 'MBS' or size_type == 'MIB':
            fileMultiplier = 1048576
        elif size_type == 'KB' or size_type == 'K' or size_type == 'KILOBYTES' or size_type == 'KBS' or size_type == 'KIB':
            fileMultiplier = 1024
        else:
            raise Invalid('Must be a valid filesize format (e.g. 123, 1.2KB, 2.5MB)')

        return int(size_number * fileMultiplier)
    else:
        raise Invalid('Must be a valid filesize format')

def format_resource_filesize(size):
    return formatters.localised_filesize(int(size))


class DataQldPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld')

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_data_driven_application': data_driven_application,
                'data_qld_dataset_data_driven_application': dataset_data_driven_application,
                'data_qld_format_resource_filesize': format_resource_filesize}

    # IValidators
    def get_validators(self):
        return {
            u'file_size_converter': file_size_converter
        }

    # IPackageController
    def set_maintainer_from_author(self, entity):
        entity.author = entity.author_email
        entity.maintainer = entity.author_email
        entity.maintainer_email = entity.author_email

    def create(self, entity):
        self.set_maintainer_from_author(entity)

    def edit(self, entity):
        self.set_maintainer_from_author(entity)