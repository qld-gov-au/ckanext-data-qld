# encoding: utf-8

import logging
import sys

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import actions
import constants
import datarequest_auth_functions as auth
import helpers
import validation

if sys.version_info[0] >= 3:
    unicode = str

if ' qa' in toolkit.config.get('ckan.plugins', ''):
    from ckanext.qa.interfaces import IQA
    import ckanext.qa.lib as qa_lib
    import ckanext.qa.tasks as qa_tasks
    import os

log = logging.getLogger(__name__)


class DataQldIntegrationPlugin(plugins.SingletonPlugin):
    """ Provide functions for integration with ckanext-datarequests and
    ckanext-validation.

    This assumes that 'data_qld_resources' is already enabled.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)

    # CKAN <= 2.7 requires just Pylons.
    # CKAN 2.8 requires a mix of Pylons and Flask.
    # CKAN 2.9 requires just Flask.
    if not toolkit.check_ckan_version(min_version='2.9.0'):
        plugins.implements(plugins.IRoutes, inherit=True)
    if toolkit.check_ckan_version(min_version='2.8.0'):
        plugins.implements(plugins.IBlueprint)

    if ' qa' in toolkit.config.get('ckan.plugins', ''):
        plugins.implements(IQA)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        schema.update({
            # This is a custom configuration option
            'ckanext.data_qld.datarequest_suggested_description': [ignore_missing, unicode],
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_datarequest_default_organisation_id': helpers.datarequest_default_organisation_id,
                'data_qld_datarequest_suggested_description': helpers.datarequest_suggested_description
                }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_scheming_choices': validation.scheming_choices
        }

    # IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            constants.UPDATE_DATAREQUEST: auth.update_datarequest,
            constants.UPDATE_DATAREQUEST_ORGANISATION: auth.update_datarequest_organisation,
            constants.CLOSE_DATAREQUEST: auth.close_datarequest,
            constants.OPEN_DATAREQUEST: auth.open_datarequest
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
    # Ignored on CKAN >= 2.9

    def before_map(self, m):
        """ Route via Pylons if blueprints aren't available yet.
        """
        if not toolkit.check_ckan_version(min_version='2.8.0'):
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

    # IBlueprint
    # Ignored on CKAN < 2.8

    def get_blueprint(self):
        import datarequest_view
        blueprints = datarequest_view.get_blueprints()
        if toolkit.check_ckan_version(min_version='2.9.0'):
            import dataset_view
            blueprints.extend(dataset_view.get_blueprints())
        return blueprints

    # IQA
    def custom_resource_score(self, resource, resource_score):
        resource_score_format = resource_score.get('format').upper() if resource_score.get('format') is not None else ''
        resource_format = resource.format.upper() if resource.format is not None else ''
        # If resource openness_score is 3 and format is CSV
        if resource_score.get('openness_score', 0) == 3 and resource_score_format == 'CSV':
            # If resource has a JSON schema which validated successfully, set score to 4
            if hasattr(resource, 'extras') and resource.extras.get('schema', None) and resource.extras.get(
                    'validation_status', '').lower() == 'success':
                resource_score['openness_score'] = 4
                resource_score['openness_score_reason'] = toolkit._(
                    'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                    .format(resource_score_format, resource_score.get('openness_score', '')))

        if resource_score.get('openness_score', 0) > 0:
            # QA cannot determine file formats that are not part of its own
            # 'resource_format_openness_scores.json' file and CKAN resource_formats.json file
            # The below are dataqld specific file formats that are not part of the default
            # CKAN resource_formats.json file and need custom scoring

            # If QA believes the resource is a TIFF file, check the resource format selected,
            # if it's GEOTIFF apply custom score
            if resource_score_format == 'TIFF' and resource_format == 'GEOTIFF':
                resource_score['openness_score'] = resource_score['openness_score'] = qa_lib.resource_format_scores().get(
                    resource_format)
                resource_score['openness_score_reason'] = toolkit._(
                    'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                    .format(resource_format, resource_score.get('openness_score', '')))

            # If QA believes the resource is a ZIP file, check the resource format selected,
            # if it's GDB apply custom score
            if resource_score_format == 'ZIP' and 'GDB' in resource_format:
                resource_score['format'] = 'GDB'
                resource_score['openness_score'] = qa_lib.resource_format_scores().get(resource_score['format'])
                resource_score['openness_score_reason'] = toolkit._(
                    'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                    .format(resource_format, resource_score.get('openness_score', '')))

            # QA by default does not know how to handle GPKG formats, check the
            # resource format selected and extension, if it's GPKG apply custom score
            if 'GPKG' in resource_format:
                if resource.url_type == 'upload' and 'GPKG' in os.path.splitext(resource.url)[1].upper() \
                        or resource.url_type == 'url' and 'GPKG' in (ext.upper() for ext in
                                                                     qa_tasks.extension_variants(resource.url)):
                    resource_score['format'] = 'GPKG'
                    resource_score['openness_score'] = qa_lib.resource_format_scores().get(resource_score['format'])
                    resource_score['openness_score_reason'] = toolkit._(
                        'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                        .format(resource_format, resource_score.get('openness_score', '')))

        return resource_score
