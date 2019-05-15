# encoding: utf-8

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import actions
import auth_functions as auth
import constants
import helpers
import converters


class DataQldPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing') 
        schema.update({
            # This is a custom configuration option
            'ckanext.data_qld.datarequest_suggested_description': [ignore_missing, unicode]
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
                'data_qld_format_activity_data': helpers.format_activity_data
                }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter            
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

    #IAuthFunctions
    def get_auth_functions(self):
        auth_functions = {
            constants.UPDATE_DATAREQUEST: auth.update_datarequest,
            constants.UPDATE_DATAREQUEST_ORGANISATION: auth.update_datarequest_organisation,
            constants.CLOSE_DATAREQUEST: auth.close_datarequest
        }
        return auth_functions
        
    #IActions
    def get_actions(self):
        additional_actions = {  
            constants.OPEN_DATAREQUEST: actions.open_datarequest,
        }
        return additional_actions

    #IRoutes
    def before_map(self, m):
       
        # Re_Open a Data Request
        m.connect('/%s/open/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.data_qld.controller:DataQldUI',
                  action='open', conditions=dict(method=['GET', 'POST']))

        return m