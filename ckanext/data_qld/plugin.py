# encoding: utf-8

import logging
import six

from ckan import plugins
import ckantoolkit as toolkit

from .de_identified_data import helpers as de_identified_data_helpers
from .dataset_deletion import helpers as dataset_deletion_helpers
from .reporting.helpers import helpers as reporting_helpers
from .reporting.logic.action import get
from .resource_freshness.helpers import helpers as resource_freshness_helpers
from .resource_freshness import validation as resource_freshness_validator
from .resource_freshness.logic.actions import get as resource_freshness_get_actions
from .resource_visibility import helpers as resource_visibility_helpers
from .resource_visibility import validators as resource_visibility_validators

import actions
import auth_functions as auth
import constants
import converters
import datarequest_auth_functions
import helpers
import validation

if ' qa' in toolkit.config.get('ckan.plugins', ''):
    from ckanext.qa.interfaces import IQA
    import ckanext.qa.lib as qa_lib
    import ckanext.qa.tasks as qa_tasks
    import os

request = toolkit.request

log = logging.getLogger(__name__)

if toolkit.check_ckan_version("2.9"):
    from flask_plugin import MixinPlugin
else:
    from pylons_plugin import MixinPlugin


class DataQldPlugin(MixinPlugin, plugins.SingletonPlugin):
    """ Provide functions specific to the Queensland Government Open Data portal.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)

    if ' qa' in toolkit.config.get('ckan.plugins', ''):
        plugins.implements(IQA)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld')
        toolkit.add_resource('reporting/fanstatic', 'data_qld_reporting')

    def update_config_schema(self, schema):
        ignore_missing = toolkit.get_validator('ignore_missing')
        schema.update({
            # This is a custom configuration option
            'ckanext.data_qld.resource_formats': [ignore_missing, six.text_type],
            'ckanext.data_qld.datarequest_suggested_description': [ignore_missing, six.text_type],
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'data_qld_datarequest_default_organisation_id': helpers.datarequest_default_organisation_id,
            'data_qld_datarequest_suggested_description': helpers.datarequest_suggested_description,
            'get_closing_circumstance_list': reporting_helpers.get_closing_circumstance_list,
            'get_organisation_list': reporting_helpers.get_organisation_list,
            'data_qld_data_driven_application': helpers.data_driven_application,
            'data_qld_dataset_data_driven_application': helpers.dataset_data_driven_application,
            'data_qld_resource_formats': helpers.resource_formats,
            'profanity_checking_enabled': helpers.profanity_checking_enabled,
            'data_qld_user_has_admin_editor_org_access': de_identified_data_helpers.user_has_admin_editor_org_access,
            'data_qld_show_de_identified_data': de_identified_data_helpers.show_de_identified_data,
            'data_qld_get_package_dict': resource_visibility_helpers.get_package_dict,
            'data_qld_get_select_field_options': resource_visibility_helpers.get_select_field_options,
            'data_qld_show_resource_visibility': resource_visibility_helpers.show_resource_visibility,
            'data_qld_update_frequencies_from_config': resource_freshness_helpers.update_frequencies_from_config,
            'data_qld_filesize_formatter': converters.filesize_formatter,
            'get_gtm_container_id': helpers.get_gtm_code,
            'get_year': helpers.get_year,
            'ytp_comments_enabled': helpers.ytp_comments_enabled,
            'is_datarequests_enabled': helpers.is_datarequests_enabled,
            'get_all_groups': helpers.get_all_groups,
            'is_request_for_resource': helpers.is_request_for_resource,
            'set_background_image_class': helpers.set_background_image_class,
            'set_external_resources': helpers.set_external_resources,
            'is_prod': helpers.is_prod,
            'comment_notification_recipients_enabled':
                helpers.get_comment_notification_recipients_enabled,
            'populate_revision': helpers.populate_revision,
            'unreplied_comments_x_days': helpers.unreplied_comments_x_days,
            'is_reporting_enabled': helpers.is_reporting_enabled,
            'members_sorted': helpers.members_sorted,
            'get_deletion_reason_template': helpers.get_deletion_reason_template
        }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_scheming_choices': validation.scheming_choices,
            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter,
            'data_qld_resource_visibility': resource_visibility_validators.resource_visibility,
            'data_qld_validate_next_update_due': resource_freshness_validator.validate_next_update_due,
            'data_qld_validate_nature_of_change_data': resource_freshness_validator.validate_nature_of_change_data,
            'data_qld_data_last_updated': resource_freshness_validator.data_last_updated,
            'data_qld_last_modified': resource_freshness_validator.last_modified,
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            constants.UPDATE_DATAREQUEST: datarequest_auth_functions.update_datarequest,
            constants.UPDATE_DATAREQUEST_ORGANISATION: datarequest_auth_functions.update_datarequest_organisation,
            constants.CLOSE_DATAREQUEST: datarequest_auth_functions.close_datarequest,
            constants.OPEN_DATAREQUEST: datarequest_auth_functions.open_datarequest,
            'has_user_permission_for_some_org': auth.has_user_permission_for_some_org,
            'has_user_permission_for_org': auth.has_user_permission_for_org
        }

    # IActions
    def get_actions(self):
        return {
            constants.OPEN_DATAREQUEST: actions.open_datarequest,
            constants.CREATE_DATAREQUEST: actions.create_datarequest,
            constants.UPDATE_DATAREQUEST: actions.update_datarequest,
            constants.CLOSE_DATAREQUEST: actions.close_datarequest,
            'organisation_followers': get.organisation_followers,
            'dataset_followers': get.dataset_followers,
            'dataset_comments': get.dataset_comments,
            'dataset_comment_followers': get.dataset_comment_followers,
            'datasets_min_one_comment_follower': get.datasets_min_one_comment_follower,
            'datarequests_min_one_comment_follower': get.datarequests_min_one_comment_follower,
            'datarequests': get.datarequests,
            'datarequest_comments': get.datarequest_comments,
            'dataset_comments_no_replies_after_x_days': get.dataset_comments_no_replies_after_x_days,
            'datarequests_no_replies_after_x_days': get.datarequests_no_replies_after_x_days,
            'datarequests_for_circumstance': get.datarequests_for_circumstance,
            'open_datarequests_no_comments_after_x_days': get.open_datarequests_no_comments_after_x_days,
            'datarequests_open_after_x_days': get.datarequests_open_after_x_days,
            'comments_no_replies_after_x_days': get.comments_no_replies_after_x_days,
            'de_identified_datasets': get.de_identified_datasets,
            'overdue_datasets': get.overdue_datasets,
            'data_qld_get_dataset_due_to_publishing': resource_freshness_get_actions.dataset_due_to_publishing,
            'data_qld_get_dataset_overdue': resource_freshness_get_actions.dataset_overdue,
            'data_qld_process_dataset_due_to_publishing': resource_freshness_get_actions.process_dataset_due_to_publishing,
            'data_qld_process_dataset_overdue': resource_freshness_get_actions.process_dataset_overdue
        }

    # IPackageController
    def after_show(self, context, data_dict):
        # system processes should have access to all resources
        if context.get('ignore_auth', False) is not True:
            de_identified_data_helpers.process_de_identified_data_dict(data_dict, helpers.get_user())
            resource_visibility_helpers.process_resources(data_dict, helpers.get_user())
        resource_freshness_helpers.process_next_update_due(data_dict)

    def after_search(self, search_results, search_params):
        for data_dict in search_results.get('results', []):
            de_identified_data_helpers.process_de_identified_data_dict(data_dict, helpers.get_user())
            resource_visibility_helpers.process_resources(data_dict, helpers.get_user())
            resource_freshness_helpers.process_next_update_due(data_dict)
        return search_results

    def delete(self, data_dict):
        dataset_deletion_helpers.add_deletion_of_dataset_reason(data_dict)

    # IResourceController
    def before_create(self, context, data_dict):
        self._check_file_upload(data_dict)

    def before_update(self, context, current_resource, updated_resource):
        self._check_file_upload(updated_resource)
        resource_freshness_helpers.check_resource_data(current_resource, updated_resource, context)

    def before_show(self, resource_dict):
        resource_freshness_helpers.process_nature_of_change(resource_dict)
        # CKAN background jobs that call 'package_show` will not have request objects
        if hasattr(request, 'params') and toolkit.get_endpoint()[1] == 'action' and 'package_show' not in request.path:
            resource_visibility_helpers.process_resource_visibility(resource_dict)

    def _check_file_upload(self, data_dict):
        # This method is to fix a bug that the ckanext-scheming creates for setting the file size of an uploaded
        # resource. Currently the actions resource_create and resource_update will only set the resource size if the
        # key does not exist in the data_dict.
        # So we will check if the resource is a file upload and remove the 'size' dictionary item from the data_dict.
        # The action resource_create and resource_update will then set the data_dict['size'] = upload.filesize if
        # 'size' not in data_dict.
        file_upload = data_dict.get(u'upload', None)
        if helpers.is_uploaded_file(file_upload):
            data_dict.pop(u'size', None)

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


class PlaceholderPlugin(plugins.SingletonPlugin):
    """ Sinkhole for deprecated plugin definitions.
    """
