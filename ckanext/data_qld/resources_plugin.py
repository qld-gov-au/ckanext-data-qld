# encoding: utf-8

import cgi
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import auth_functions as auth
import converters
import helpers
import logging

log = logging.getLogger(__name__)


class DataQldResourcesPlugin(plugins.SingletonPlugin):
    """ Provide this plugin's resources without adding dependencies
    eg don't force integration with other extensions.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_resource('fanstatic', 'data_qld')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        schema.update({
            'ckanext.data_qld.resource_formats': [ignore_missing, unicode]
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_data_driven_application': helpers.data_driven_application,
                'data_qld_dataset_data_driven_application': helpers.dataset_data_driven_application,
                'data_qld_organisation_list': helpers.organisation_list,
                'data_qld_user_has_admin_access': helpers.user_has_admin_access,
                'data_qld_format_activity_data': helpers.format_activity_data,
                'data_qld_resource_formats': helpers.resource_formats
                }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter,
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

    # IAuthFunctions
    def get_auth_functions(self):
        return {'member_create': auth.member_create}

    # IResourceController
    def before_create(self, context, data_dict):
        return self.check_file_upload(data_dict)

    def before_update(self, context, current_resource, updated_resource):
        return self.check_file_upload(updated_resource)

    def check_file_upload(self, data_dict):
        # This method is to fix a bug that the ckanext-scheming creates for setting the file size of an uploaded
        # resource. Currently the actions resource_create and resource_update will only set the resource size if the
        # key does not exist in the data_dict.
        # So we will check if the resource is a file upload and remove the 'size' dictionary item from the data_dict.
        # The action resource_create and resource_update will then set the data_dict['size'] = upload.filesize if
        # 'size' not in data_dict.
        file_upload = data_dict.get(u'upload', None)
        if isinstance(file_upload, cgi.FieldStorage):
            data_dict.pop(u'size', None)

        return data_dict

    def after_create(self, context, data_dict):
        # Set the resource position order for this (latest) resource to first
        resource_id = data_dict.get('id', None)
        package_id = data_dict.get('package_id', None)
        if resource_id and package_id:
            try:
                toolkit.get_action('package_resource_reorder')(context, {'id': package_id, 'order': [resource_id]})
            except Exception, e:
                log.error(str(e))
        return data_dict

    # IMiddleware
    def make_middleware(self, app, config):
        return AuthMiddleware(app, config)


class AuthMiddleware(object):
    def __init__(self, app, app_conf):
        self.app = app

    def __call__(self, environ, start_response):
        # Redirect users to /user/reset page after submitting password reset request
        if environ['PATH_INFO'] == '/' and 'HTTP_REFERER' in environ and 'user/reset' in environ['HTTP_REFERER']:
            headers = [('Location', '/user/reset')]
            status = "302 Found"
            start_response(status, headers)
            return ['']

        return self.app(environ, start_response)
