# encoding: utf-8
import sys
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader

import auth_functions as auth
import blueprint_overrides
import converters
import helpers
import logging

import ckanext.data_qld.resource_freshness.helpers.helpers as resource_freshness_helpers
import ckanext.data_qld.resource_freshness.validation as resource_freshness_validator
import ckanext.data_qld.resource_freshness.logic.actions.get as resource_freshness_get_actions

from flask import Blueprint
from ckanext.data_qld.de_identified_data import helpers as de_identified_data_helpers
from ckanext.data_qld.resource_visibility import helpers as resource_visibility_helpers
from ckanext.data_qld.resource_visibility import validators as resource_visibility_validators
from ckanext.data_qld.dataset_deletion import helpers as dataset_deletion_helpers
from ckanext.data_qld.user_creation import validators as user_creation_validators
from ckanext.data_qld.user_creation.logic.actions import create as user_creation_create_actions
from ckanext.data_qld.user_creation.logic.actions import update as user_creation_update_actions

if sys.version_info[0] >= 3:
    unicode = str

request = toolkit.request
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
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_resource('fanstatic', 'data_qld')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        schema.update({
            'ckanext.data_qld.resource_formats': [ignore_missing, unicode],
            'ckanext.data_qld.excluded_display_name_words': [ignore_missing, unicode]
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {'data_qld_data_driven_application': helpers.data_driven_application,
                'data_qld_dataset_data_driven_application': helpers.dataset_data_driven_application,
                'data_qld_organisation_list': helpers.organisation_list,
                'data_qld_user_has_admin_access': helpers.user_has_admin_access,
                'data_qld_format_activity_data': helpers.format_activity_data,
                'data_qld_resource_formats': helpers.resource_formats,
                'activity_type_nice': helpers.activity_type_nice,
                'profanity_checking_enabled': helpers.profanity_checking_enabled,
                'data_qld_user_has_admin_editor_org_access': de_identified_data_helpers.user_has_admin_editor_org_access,
                'data_qld_show_de_identified_data': de_identified_data_helpers.show_de_identified_data,
                'data_qld_get_package_dict': resource_visibility_helpers.get_package_dict,
                'data_qld_get_select_field_options': resource_visibility_helpers.get_select_field_options,
                'data_qld_show_resource_visibility': resource_visibility_helpers.show_resource_visibility,
                'data_qld_update_frequencies_from_config': resource_freshness_helpers.update_frequencies_from_config
                }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter,
            'data_qld_resource_visibility': resource_visibility_validators.resource_visibility,
            'data_qld_validate_next_update_due': resource_freshness_validator.validate_next_update_due,
            'data_qld_validate_nature_of_change_data': resource_freshness_validator.validate_nature_of_change_data,
            'data_qld_data_last_updated': resource_freshness_validator.data_last_updated,
            'data_qld_user_name_validator': user_creation_validators.data_qld_user_name_validator,
            'data_qld_displayed_name_validator': user_creation_validators.data_qld_displayed_name_validator
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

    def after_show(self, context, data_dict):
        de_identified_data_helpers.process_de_identified_data_dict(data_dict, toolkit.g.userobj)
        resource_visibility_helpers.process_resources(data_dict, toolkit.g.userobj)
        resource_freshness_helpers.process_next_update_due(data_dict)

    def after_search(self, search_results, search_params):
        for data_dict in search_results.get('results', []):
            de_identified_data_helpers.process_de_identified_data_dict(data_dict, toolkit.g.userobj)
            resource_visibility_helpers.process_resources(data_dict, toolkit.g.userobj)
            resource_freshness_helpers.process_next_update_due(data_dict)
        return search_results

    def delete(self, data_dict):
        dataset_deletion_helpers.add_deletion_of_dataset_reason(data_dict)

    # IAuthFunctions
    def get_auth_functions(self):
        return {'member_create': auth.member_create}

    # IResourceController
    def before_create(self, context, data_dict):
        self.check_file_upload(data_dict)

    def before_update(self, context, current_resource, updated_resource):
        self.check_file_upload(updated_resource)
        resource_freshness_helpers.check_resource_data(current_resource, updated_resource, context)

    def before_show(self, resource_dict):
        resource_freshness_helpers.process_nature_of_change(resource_dict)
        # CKAN background jobs that call 'package_show` will not have request objects
        if hasattr(request, 'params') and toolkit.get_endpoint()[1] == 'action' and 'package_show' not in request.path:
            resource_visibility_helpers.process_resource_visibility(resource_dict)

    def check_file_upload(self, data_dict):
        # This method is to fix a bug that the ckanext-scheming creates for setting the file size of an uploaded
        # resource. Currently the actions resource_create and resource_update will only set the resource size if the
        # key does not exist in the data_dict.
        # So we will check if the resource is a file upload and remove the 'size' dictionary item from the data_dict.
        # The action resource_create and resource_update will then set the data_dict['size'] = upload.filesize if
        # 'size' not in data_dict.
        file_upload = data_dict.get(u'upload', None)
        if isinstance(file_upload, uploader.ALLOWED_UPLOAD_TYPES):
            data_dict.pop(u'size', None)

    def after_create(self, context, data_dict):
        # Set the resource position order for this (latest) resource to first
        resource_id = data_dict.get('id', None)
        package_id = data_dict.get('package_id', None)
        if resource_id and package_id:
            try:
                toolkit.get_action('package_resource_reorder')(context, {'id': package_id, 'order': [resource_id]})
            except Exception as e:
                log.error(str(e))

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

    # IActions
    def get_actions(self):
        return {
            'user_create': user_creation_create_actions.user_create,
            'user_update': user_creation_update_actions.user_update,
            'data_qld_get_dataset_due_to_publishing': resource_freshness_get_actions.dataset_due_to_publishing,
            'data_qld_get_dataset_overdue': resource_freshness_get_actions.dataset_overdue,
            'data_qld_process_dataset_due_to_publishing': resource_freshness_get_actions.process_dataset_due_to_publishing,
            'data_qld_process_dataset_overdue': resource_freshness_get_actions.process_dataset_overdue
        }
