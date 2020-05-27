# encoding: utf-8

import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import actions
import constants
import datarequest_auth_functions as auth
import helpers
import validation

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
    plugins.implements(plugins.IRoutes, inherit=True)

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
                'data_qld_datarequest_suggested_description': helpers.datarequest_suggested_description,
                'get_content_type_comments_badge': helpers.get_content_type_comments_badge
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
    def before_map(self, m):
        # Re_Open a Data Request
        m.connect('/%s/open/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.data_qld.controller:DataQldUI',
                  action='open_datarequest', conditions=dict(method=['GET', 'POST']))

        m.connect('/dataset/{dataset_id}/resource/{resource_id}/%s/show/' % constants.SCHEMA_MAIN_PATH,
                  controller='ckanext.data_qld.controller:DataQldUI',
                  action='show_schema', conditions=dict(method=['GET']))

        return m
