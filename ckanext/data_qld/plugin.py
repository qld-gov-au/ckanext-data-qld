# encoding: utf-8

import cgi
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import actions
import auth_functions as auth
import blueprint_overrides
import constants
import datarequest_auth_functions as datareq_auth
import converters
import helpers
import validation

from flask import Blueprint

if "qa" in toolkit.config.get('ckan.plugins', False):
    from ckanext.qa.interfaces import IQA
    import ckanext.qa.lib as qa_lib
    import ckanext.qa.tasks as qa_tasks
    import os

log = logging.getLogger(__name__)


class DataQldPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(plugins.IMiddleware, inherit=True)
    plugins.implements(plugins.IBlueprint)
    if "qa" in toolkit.config.get('ckan.plugins', False):
        plugins.implements(IQA)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        schema.update({
            # This is a custom configuration option
            'ckanext.data_qld.datarequest_suggested_description': [ignore_missing, unicode],
            'ckanext.data_qld.resource_formats': [ignore_missing, unicode]
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_data_driven_application': helpers.data_driven_application,
                'data_qld_dataset_data_driven_application': helpers.dataset_data_driven_application,
                'data_qld_datarequest_default_organisation_id': helpers.datarequest_default_organisation_id,
                'data_qld_organisation_list': helpers.organisation_list,
                'data_qld_datarequest_suggested_description': helpers.datarequest_suggested_description,
                'data_qld_user_has_admin_access': helpers.user_has_admin_access,
                'data_qld_format_activity_data': helpers.format_activity_data,
                'data_qld_resource_formats': helpers.resource_formats,
                'activity_type_nice': helpers.activity_type_nice,
                'profanity_checking_enabled': helpers.profanity_checking_enabled
                }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter,
            'data_qld_scheming_choices': validation.scheming_choices,
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
        auth_functions = {
            constants.UPDATE_DATAREQUEST: datareq_auth.update_datarequest,
            constants.UPDATE_DATAREQUEST_ORGANISATION: datareq_auth.update_datarequest_organisation,
            constants.CLOSE_DATAREQUEST: datareq_auth.close_datarequest,
            constants.OPEN_DATAREQUEST: datareq_auth.open_datarequest,
            'member_create': auth.member_create
        }
        return auth_functions

    # IActions
    def get_actions(self):
        additional_actions = {
            constants.OPEN_DATAREQUEST: actions.open_datarequest,
            constants.CREATE_DATAREQUEST: actions.create_datarequest,
            constants.UPDATE_DATAREQUEST: actions.update_datarequest,
            constants.CLOSE_DATAREQUEST: actions.close_datarequest,
        }
        return additional_actions

    # IRoutes
    def before_map(self, m):
        # Re_Open a Data Request
        m.connect('/%s/open/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.data_qld.controller:DataQldUI',
                  action='open_datarequest', conditions=dict(method=['GET', 'POST']))

        m.connect('/dataset/{dataset_id}/resource/{resource_id}/%s/show/' % constants.SCHEMA_MAIN_PATH,
                  controller='ckanext.data_qld.controller:DataQldUI',
                  action='show_schema', conditions=dict(method=['GET']))

        # This is a pain, but re-assigning the dataset_read route using `before_map`
        # appears to affect these two routes, so we need to replicate them here
        m.connect('dataset_new', '/dataset/new', controller='package', action='new')
        m.connect('/dataset/{action}',
                  controller='ckan.controllers.package',
                  requirements=dict(action='|'.join([
                      'list',
                      'autocomplete',
                      'search'
                  ])))

        # Currently no dataset/package blueprint available, so we need to override these core routes
        m.connect('dataset_read', '/dataset/{id}',
                  controller='ckanext.data_qld.controller:DataQldDataset',
                  action='read',
                  ckan_icon='sitemap')
        m.connect('/dataset/{id}/resource/{resource_id}',
                  controller='ckanext.data_qld.controller:DataQldDataset',
                  action='resource_read')

        return m

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

    # IBlueprint
    def get_blueprint(self):
        """
        CKAN uses Flask Blueprints in the /ckan/views dir for user and dashboard
        Here we override some routes to redirect unauthenticated users to the login page, and only redirect the
        user to the `came_from` URL if they are logged in.
        :return:
        """
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.add_url_rule(u'/user/logged_in', u'logged_in', blueprint_overrides.logged_in_override)
        blueprint.add_url_rule(u'/user/edit', u'edit', blueprint_overrides.user_edit_override)
        blueprint.add_url_rule(
            u'/dashboard/', u'dashboard', blueprint_overrides.dashboard_override, strict_slashes=False, defaults={
                u'offset': 0
            })
        return blueprint

    # IQA
    def custom_resource_score(self, resource, resource_score):
        resource_score_format = resource_score.get('format').upper() if resource_score.get('format') is not None else ''
        resource_format = resource.format.upper() if resource.format is not None else ''
        # If resource openness_score is 3 and format is CSV
        if resource_score.get('openness_score', 0) == 3 and resource_score_format == 'CSV':
            # If resource has a JSON schema which validated successfully, set score to 4
            if hasattr(resource, 'extras') and resource.extras.get('schema', None) and resource.extras.get('validation_status', None) == 'success':
                resource_score['openness_score'] = 4
                resource_score['openness_score_reason'] = toolkit._('Content of file appeared to be format "{0}" which receives openness score: {1}.'
                                                                    .format(resource_score_format, resource_score.get('openness_score', '')))

        # QA cannot determine file formats that are not part of its own 'resource_format_openness_scores.json' file and CKAN resource_formats.json file
        # The below are dataqld specific file formats that are not part of the default CKAN resource_formats.json file and need custom scoring

        # If QA believes the resource is a TIFF file, check the resource format selected, if its GEOTIFF apply custom score
        if resource_score_format == 'TIFF' and resource_format == 'GEOTIFF':
            resource_score['openness_score'] = resource_score['openness_score'] = qa_lib.resource_format_scores().get(resource_format)
            resource_score['openness_score_reason'] = toolkit._('Content of file appeared to be format "{0}" which receives openness score: {1}.'
                                                                .format(resource_format, resource_score.get('openness_score', '')))

        # If QA believes the resource is a ZIP file, check the resource format selected, if its GDB apply custom score
        if resource_score_format == 'ZIP' and 'GDB' in resource_format:
            resource_score['format'] = 'GDB'
            resource_score['openness_score'] = qa_lib.resource_format_scores().get(resource_score['format'])
            resource_score['openness_score_reason'] = toolkit._('Content of file appeared to be format "{0}" which receives openness score: {1}.'
                                                                .format(resource_format, resource_score.get('openness_score', '')))

        # QA by default does not know how to handle GPKG formats, check the resource format selected and extension, if its GPKG apply custom score
        log.debug('url: {0}'.format(resource.url))
        log.debug('url: {0}'.format(qa_tasks.extension_variants(resource.url)))
        if 'GPKG' in resource_format:
            if resource.url_type == 'upload' and 'GPKG' in os.path.splitext(resource.url)[1].upper() \
                    or resource.url_type == 'url' and 'GPKG' in (ext.upper() for ext in qa_tasks.extension_variants(resource.url)):
                resource_score['format'] = 'GPKG'
                resource_score['openness_score'] = qa_lib.resource_format_scores().get(resource_score['format'])
                resource_score['openness_score_reason'] = toolkit._('Content of file appeared to be format "{0}" which receives openness score: {1}.'
                                                                    .format(resource_format, resource_score.get('openness_score', '')))

        return resource_score


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
