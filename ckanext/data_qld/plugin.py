# encoding: utf-8

import datetime
import logging
import six
from six.moves.urllib.parse import urlencode

from ckan import model, plugins
from ckan.lib.helpers import json
import ckantoolkit as tk

try:
    from ckanext.qa.interfaces import IQA
    import ckanext.qa.lib as qa_lib
    import ckanext.qa.tasks as qa_tasks
    import os
    qa_present = True
except ImportError:
    qa_present = False

from ckanext.validation.interfaces import IDataValidation
from ckanext.resource_visibility import auth_functions as visibility_auth_functions
from ckanext.resource_visibility.constants import FIELD_DE_IDENTIFIED, YES

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.ckanharvester import CKANHarvester, ContentFetchError, SearchError

from . import actions, blueprints, click_cli, \
    constants, converters, datarequest_auth_functions, helpers, validation

from .dataset_deletion import helpers as dataset_deletion_helpers
from .reporting import blueprints as reporting_blueprints
from .reporting.helpers import helpers as reporting_helpers
from .reporting.logic.action import get
from .resource_freshness.helpers import helpers as resource_freshness_helpers
from .resource_freshness import validation as resource_freshness_validator
from .resource_freshness.logic.actions import get as resource_freshness_get_actions

log = logging.getLogger(__name__)


class DataQldPlugin(CKANHarvester):
    """ Provide functions specific to the Queensland Government Open Data portal.
    """
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.ITemplateHelpers, inherit=True)
    plugins.implements(plugins.IValidators)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IResourceController, inherit=True)
    plugins.implements(IDataValidation, inherit=True)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)

    if qa_present:
        plugins.implements(IQA)

    # IConfigurer
    def update_config(self, config_):
        config_.update({
            'ckanext.datarequests.notify_all_members': False,
            'ckanext.datarequests.notify_on_update': True
        })
        tk.add_template_directory(config_, 'templates')
        tk.add_public_directory(config_, 'public')
        tk.add_resource('fanstatic', 'data_qld_theme')
        tk.add_resource('reporting/fanstatic', 'data_qld_reporting')
        actions.intercept()

    def update_config_schema(self, schema):
        ignore_missing = tk.get_validator('ignore_missing')
        unicode_safe = tk.get_validator('unicode_safe')
        schema.update({
            # This is a custom configuration option
            'ckanext.data_qld.resource_formats': [ignore_missing, unicode_safe],
            'ckanext.data_qld.datarequest_suggested_description': [ignore_missing, unicode_safe],
        })
        return schema

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'data_qld_datarequest_default_organisation_id': helpers.datarequest_default_organisation_id,
            'data_qld_datarequest_suggested_description': helpers.datarequest_suggested_description,
            'get_closing_circumstance_list': reporting_helpers.get_closing_circumstance_list,
            'get_organisation_list': reporting_helpers.get_organisation_list,
            'get_deidentified_count_from_date_display': reporting_helpers.get_deidentified_count_from_date_display,
            'data_qld_data_driven_application': helpers.data_driven_application,
            'data_qld_dataset_data_driven_application': helpers.dataset_data_driven_application,
            'data_qld_resource_formats': helpers.resource_formats,
            'profanity_checking_enabled': helpers.profanity_checking_enabled,
            'data_qld_update_frequencies_from_config': resource_freshness_helpers.update_frequencies_from_config,
            'data_qld_filesize_formatter': converters.filesize_formatter,
            'get_gtm_container_id': helpers.get_gtm_code,
            'get_year': helpers.get_year,
            'ytp_comments_enabled': helpers.ytp_comments_enabled,
            'dashboard_index_route': helpers.dashboard_index_route,
            'is_datarequests_enabled': helpers.is_datarequests_enabled,
            'is_request_for_resource': helpers.is_request_for_resource,
            'set_background_image_class': helpers.set_background_image_class,
            'set_external_resources': helpers.set_external_resources,
            'is_prod': helpers.is_prod,
            'comment_notification_recipients_enabled':
                helpers.get_comment_notification_recipients_enabled,
            'unreplied_comments_x_days': helpers.unreplied_comments_x_days,
            'is_reporting_enabled': helpers.is_reporting_enabled,
            'members_sorted': helpers.members_sorted,
            'get_deletion_reason_template': helpers.get_deletion_reason_template,
            'check_ckan_version': tk.check_ckan_version,
            'is_apikey_enabled': helpers.is_apikey_enabled,
        }

    # IValidators
    def get_validators(self):
        return {
            'data_qld_scheming_choices': validation.scheming_choices,
            'data_qld_process_schema_fields': validation.process_schema_fields,
            'data_qld_align_default_schema': validation.align_default_schema,
            'data_qld_check_schema_alignment': validation.check_schema_alignment,
            'data_qld_check_schema_alignment_default_schema': validation.check_schema_alignment_default_schema,

            'data_qld_filesize_converter': converters.filesize_converter,
            'data_qld_filesize_formatter': converters.filesize_formatter,

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
            'has_user_permission_for_some_org': visibility_auth_functions.has_user_permission_for_some_org,
            'has_user_permission_for_org': visibility_auth_functions.has_user_permission_for_org
        }

    # IActions
    def get_actions(self):
        return {
            constants.OPEN_DATAREQUEST: actions.open_datarequest,
            constants.LIST_DATAREQUESTS: actions.list_datarequests,
            'package_search': actions.package_search,
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
            'de_identified_datasets_no_schema': get.de_identified_datasets_no_schema,
            'de_identified_datasets': get.de_identified_datasets,
            'overdue_datasets': get.overdue_datasets,
            'datasets_no_groups': get.datasets_no_groups,
            'datasets_no_tags': get.datasets_no_tags,
            'resources_pending_privacy_assessment': get.resources_pending_privacy_assessment,
            'data_qld_get_dataset_due_to_publishing': resource_freshness_get_actions.dataset_due_to_publishing,
            'data_qld_get_dataset_overdue': resource_freshness_get_actions.dataset_overdue,
            'data_qld_process_dataset_due_to_publishing': resource_freshness_get_actions.process_dataset_due_to_publishing,
            'data_qld_process_dataset_overdue': resource_freshness_get_actions.process_dataset_overdue
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
        # system processes should have access to all resources
        if context.get('ignore_auth', False) is not True:
            resource_freshness_helpers.process_next_update_due(data_dict)

    def after_search(self, search_results, search_params):
        for data_dict in search_results.get('results', []):
            resource_freshness_helpers.process_next_update_due(data_dict)
        return search_results

    def after_delete(self, context, data_dict):
        if isinstance(data_dict, dict):
            dataset_deletion_helpers.add_deletion_of_dataset_reason(
                context, data_dict)

    # IResourceController
    def before_create(self, context, data_dict):
        self._check_file_upload(data_dict)

    def before_update(self, context, current_resource, updated_resource):
        self._check_file_upload(updated_resource)
        resource_freshness_helpers.check_resource_data(
            current_resource, updated_resource, context)

    def before_show(self, resource_dict):
        resource_freshness_helpers.process_nature_of_change(resource_dict)

    def before_index(self, pkg_dict):
        # Return untouched
        return pkg_dict

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
        resource_score_format = resource_score.get('format').upper(
        ) if resource_score.get('format') is not None else ''
        resource_format = resource.format.upper() if resource.format is not None else ''
        # If resource openness_score is 3 and format is CSV
        if resource_score.get('openness_score', 0) == 3 and resource_score_format == 'CSV':
            # If resource has a JSON schema which validated successfully, set score to 4
            if hasattr(resource, 'extras') and resource.extras.get('schema', None) and resource.extras.get(
                    'validation_status', '').lower() == 'success':
                resource_score['openness_score'] = 4
                resource_score['openness_score_reason'] = tk._(
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
                resource_score['openness_score_reason'] = tk._(
                    'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                    .format(resource_format, resource_score.get('openness_score', '')))

            # If QA believes the resource is a ZIP file, check the resource format selected,
            # if it's GDB apply custom score
            if resource_score_format == 'ZIP' and 'GDB' in resource_format:
                resource_score['format'] = 'GDB'
                resource_score['openness_score'] = qa_lib.resource_format_scores().get(
                    resource_score['format'])
                resource_score['openness_score_reason'] = tk._(
                    'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                    .format(resource_format, resource_score.get('openness_score', '')))

            # QA by default does not know how to handle GPKG formats, check the
            # resource format selected and extension, if it's GPKG apply custom score
            if 'GPKG' in resource_format:
                if resource.url_type == 'upload' and 'GPKG' in os.path.splitext(resource.url)[1].upper() \
                        or resource.url_type == 'url' and 'GPKG' in (ext.upper() for ext in
                                                                     qa_tasks.extension_variants(resource.url)):
                    resource_score['format'] = 'GPKG'
                    resource_score['openness_score'] = qa_lib.resource_format_scores().get(
                        resource_score['format'])
                    resource_score['openness_score_reason'] = tk._(
                        'Content of file appeared to be format "{0}" which receives openness score: {1}.'
                        .format(resource_format, resource_score.get('openness_score', '')))

        return resource_score

    # IDataValidation

    def set_create_mode(self, context, data_dict, current_mode):
        if data_dict.get('schema') and self._is_de_identified(data_dict):
            return "sync"
        return current_mode

    def set_update_mode(self, context, data_dict, current_mode):
        if data_dict.get('schema') and self._is_de_identified(data_dict):
            return "sync"
        return current_mode

    def _is_de_identified(self, data_dict):
        pkg_id = data_dict.get(u'package_id')
        pkg_dict = tk.get_action(u'package_show')(
            {'ignore_auth': True}, {u'id': pkg_id})

        return pkg_dict.get(FIELD_DE_IDENTIFIED) == YES

    # IBlueprint

    def get_blueprint(self):
        return [blueprints.blueprint, reporting_blueprints.blueprint]

    # IClick

    def get_commands(self):
        return click_cli.get_commands()

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['dataset_type'] = tk._('Data Portals')
        facets_dict.move_to_end('dataset_type', last=False)
        return facets_dict

    # CKANHarvester
    config = None

    def info(self):
        return {
            'name': 'geoscience_ckan_harvester',
            'title': 'GSQ Open Data Portal',
            'description': 'Harvests the remote CKAN instance of GSQ Open Data Portal datasets into Data QLD Open Data portal schema',
            'form_config_interface': 'Text'
        }

    def validate_config(self, config):
        if not config:
            raise ValueError('No config set')
        {
            "dataset_type": "geoscience",
            "license_id": "cc-by-4",
            "security_classification": "PUBLIC",
            "version": "1.0",
            "update_frequency": "non-regular",
            "data_driven_application": "NO",
            "de_identified_data": "NO",
            "default_groups": ["Geoscience"],
            "deletion_reason": "Dataset deleted at harvest source",
            "author_email": "gsqopendata@resources.qld.gov.au",
        }

        try:
            config_obj = json.loads(config)

            if 'default_groups' in config_obj:
                if not isinstance(config_obj['default_groups'], list):
                    raise ValueError('default_groups must be a *list* of group'
                                     ' names/ids')
                if config_obj['default_groups'] and \
                        not isinstance(config_obj['default_groups'][0],
                                       six.string_types):
                    raise ValueError('default_groups must be a list of group '
                                     'names/ids (i.e. strings)')

                # Check if default groups exist
                context = {'model': model, 'user': tk.g.user}
                config_obj['default_group_dicts'] = []
                for group_name_or_id in config_obj['default_groups']:
                    try:
                        group = tk.get_action('group_show')(
                            context, {'id': group_name_or_id})
                        # save the dict to the config object, as we'll need it
                        # in the import_stage of every dataset
                        config_obj['default_group_dicts'].append(group)
                    except tk.ObjectNotFound:
                        raise ValueError('Default group not found')

                config = json.dumps(config_obj)

            if 'dataset_type' not in config_obj:
                raise ValueError('dataset_type must be set')

            if 'license_id' not in config_obj:
                raise ValueError('license_id must be set')

            if 'security_classification' not in config_obj:
                raise ValueError('security_classification must be set')

            if 'version' not in config_obj:
                raise ValueError('version must be set')

            if 'update_frequency' not in config_obj:
                raise ValueError('update_frequency must be set')

            if 'data_driven_application' not in config_obj:
                raise ValueError('data_driven_application must be set')

            if 'de_identified_data' not in config_obj:
                raise ValueError('de_identified_data must be set')

            if 'deletion_reason' not in config_obj:
                raise ValueError('deletion_reason must be set')

            if 'author_email' not in config_obj:
                raise ValueError('author_email must be set')

        except ValueError as e:
            raise e

        return config

    def modify_package_dict(self, package_dict, harvest_object):

        self._set_config(harvest_object.job.source.config)

        # Set dataset url back to source
        package_dict['url'] = '{0}/dataset/{1}'.format(harvest_object.source.url.rstrip('/'), package_dict.get('name'))
        package_dict['notes'] = u'URL: {0}\r\n\r\n{1}'.format(package_dict.get('url'), package_dict.get('notes', '') or '')

        #  Set default values from harvest config
        if not package_dict.get('version'):
            package_dict['version'] = self.config.get('version')
        package_dict['author_email'] = package_dict.get('extra:contact_uri') or self.config.get('author_email')

        package_dict['type'] = self.config.get('dataset_type')
        package_dict['license_id'] = self.config.get('license_id')
        package_dict['security_classification'] = self.config.get('security_classification')
        package_dict['data_driven_application'] = self.config.get('data_driven_application')
        package_dict['update_frequency'] = self.config.get('update_frequency')
        package_dict['de_identified_data'] = self.config.get('de_identified_data')
        package_dict['groups'] = self.config.get('default_group_dicts')

        # Loop through the resources to compare data_last_updated field with last_modified
        data_last_updated = package_dict.get('data_last_updated')
        data_last_updated = tk.get_validator('isodate')(data_last_updated, {}) if data_last_updated else None
        for resource in package_dict.get('resources', []):
            try:
                resource_last_modified = resource.get('last_modified') or resource.get('metadata_modified')
                last_modified = tk.get_validator('isodate')(resource_last_modified, {})
            except tk.Invalid:
                log.warning('Invalid resource %s date format %s for harvest object %s ',
                            resource.get('id'), resource_last_modified, harvest_object.id)
                continue
            if data_last_updated is None or last_modified > data_last_updated:
                data_last_updated = last_modified
        package_dict['data_last_updated'] = data_last_updated.isoformat() if isinstance(data_last_updated, datetime.datetime) else None

        # Remove metadata we do not want to harvest
        package_dict.pop('extras', [])
        package_dict.pop('resources', [])

        return package_dict

    def gather_stage(self, harvest_job):
        '''
            This is copied from the default CKANHarvester 'gather_stage' https://github.com/ckan/ckanext-harvest/blob/3793480a91b9eedc13c34f055e2a94aca5c7e045/ckanext/harvest/harvesters/ckanharvester.py#L182
            It has one small modification, which is to move the creation of the harvest objects from the end of the 'gather_stage' https://github.com/ckan/ckanext-harvest/blob/3793480a91b9eedc13c34f055e2a94aca5c7e045/ckanext/harvest/harvesters/ckanharvester.py#L268
            This has now been moved into the end of the method '_search_for_datasets', once its retrieved the dataset results it will now create the harvest objects '_create_harvest_objects'
            The default behaviour was to retrieve all the datasets from the source and store them in a list in memory before creating the harvest objects which caused memory issues when there was a large amount of datasets retrieved eg 100,000+
            The solution is to instead of addding the datasets to a list as it pages through the API call, it will now create the harvest objects straight away once the datasets have been retrieved so there are no memory issues.
        '''
        log.debug('In CKANHarvester gather_stage (%s)',
                  harvest_job.source.url)
        get_all_packages = True

        self._set_config(harvest_job.source.config)

        # Get source URL
        remote_ckan_base_url = harvest_job.source.url.rstrip('/')

        # Filter in/out datasets from particular organizations
        fq_terms = []
        org_filter_include = self.config.get('organizations_filter_include', [])
        org_filter_exclude = self.config.get('organizations_filter_exclude', [])
        if org_filter_include:
            fq_terms.append(' OR '.join(
                'organization:%s' % org_name for org_name in org_filter_include))
        elif org_filter_exclude:
            fq_terms.extend(
                '-organization:%s' % org_name for org_name in org_filter_exclude)

        groups_filter_include = self.config.get('groups_filter_include', [])
        groups_filter_exclude = self.config.get('groups_filter_exclude', [])
        if groups_filter_include:
            fq_terms.append(' OR '.join(
                'groups:%s' % group_name for group_name in groups_filter_include))
        elif groups_filter_exclude:
            fq_terms.extend(
                '-groups:%s' % group_name for group_name in groups_filter_exclude)

        # Ideally we can request from the remote CKAN only those datasets
        # modified since the last completely successful harvest.
        last_error_free_job = self.last_error_free_job(harvest_job)
        log.debug('Last error-free job: %r', last_error_free_job)
        if (last_error_free_job and not self.config.get('force_all', False)):
            get_all_packages = False

            # Request only the datasets modified since
            last_time = last_error_free_job.gather_started
            # Note: SOLR works in UTC, and gather_started is also UTC, so
            # this should work as long as local and remote clocks are
            # relatively accurate. Going back a little earlier, just in case.
            get_changes_since = \
                (last_time - datetime.timedelta(hours=1)).isoformat()
            log.info('Searching for datasets modified since: %s UTC',
                     get_changes_since)

            fq_since_last_time = 'metadata_modified:[{since}Z TO *]' \
                .format(since=get_changes_since)

            try:
                object_ids = self._search_for_datasets(
                    harvest_job,
                    remote_ckan_base_url,
                    fq_terms + [fq_since_last_time])
            except SearchError as e:
                log.info('Searching for datasets changed since last time '
                         'gave an error: %s', e)
                get_all_packages = True

            if not get_all_packages and not object_ids:
                log.info('No datasets have been updated on the remote '
                         'CKAN instance since the last harvest job %s',
                         last_time)
                return []

        # Fall-back option - request all the datasets from the remote CKAN
        if get_all_packages:
            # Request all remote packages
            try:
                object_ids = self._search_for_datasets(harvest_job,
                                                       remote_ckan_base_url,
                                                       fq_terms)
            except SearchError as e:
                log.info('Searching for all datasets gave an error: %s', e)
                self._save_gather_error(
                    'Unable to search remote CKAN for datasets:%s url:%s'
                    'terms:%s' % (e, remote_ckan_base_url, fq_terms),
                    harvest_job)
                return None
        if not object_ids:
            self._save_gather_error(
                'No datasets found at CKAN: %s' % remote_ckan_base_url,
                harvest_job)
            return []

        return object_ids

    def _search_for_datasets(self, harvest_job, remote_ckan_base_url, fq_terms=None):
        '''Does a dataset search on a remote CKAN and returns the results.

        Deals with paging to return all the results, not just the first page.
        '''
        base_search_url = remote_ckan_base_url + self._get_search_api_offset()
        params = {'rows': '1000', 'start': '0'}
        # There is the worry that datasets will be changed whilst we are paging
        # through them.
        # * In SOLR 4.7 there is a cursor, but not using that yet
        #   because few CKANs are running that version yet.
        # * However we sort, then new names added or removed before the current
        #   page would cause existing names on the next page to be missed or
        #   double counted.
        # * Another approach might be to sort by metadata_modified and always
        #   ask for changes since (and including) the date of the last item of
        #   the day before. However if the entire page is of the exact same
        #   time, then you end up in an infinite loop asking for the same page.
        # * We choose a balanced approach of sorting by ID, which means
        #   datasets are only missed if some are removed, which is far less
        #   likely than any being added. If some are missed then it is assumed
        #   they will harvested the next time anyway. When datasets are added,
        #   we are at risk of seeing datasets twice in the paging, so we detect
        #   and remove any duplicates.
        params['sort'] = 'id asc'
        if fq_terms:
            params['fq'] = ' '.join(fq_terms)

        object_ids = []
        pkg_ids = set()
        previous_content = None
        while True:
            url = base_search_url + '?' + urlencode(params)
            log.debug('Searching for CKAN datasets: %s', url)
            try:
                content = self._get_content(url)
            except ContentFetchError as e:
                raise SearchError(
                    'Error sending request to search remote '
                    'CKAN instance %s using URL %r. Error: %s' %
                    (remote_ckan_base_url, url, e))

            if previous_content and content == previous_content:
                raise SearchError('The paging doesn\'t seem to work. URL: %s' %
                                  url)
            try:
                response_dict = json.loads(content)
            except ValueError:
                raise SearchError('Response from remote CKAN was not JSON: %r'
                                  % content)
            try:
                pkg_dicts_page = response_dict.get('result', {}).get('results',
                                                                     [])
            except ValueError:
                raise SearchError('Response JSON did not contain '
                                  'result/results: %r' % response_dict)

            # Weed out any datasets found on previous pages (should datasets be
            # changing while we page)
            ids_in_page = set(p['id'] for p in pkg_dicts_page)
            duplicate_ids = ids_in_page & pkg_ids
            if duplicate_ids:
                pkg_dicts_page = [p for p in pkg_dicts_page
                                  if p['id'] not in duplicate_ids]
            pkg_ids |= ids_in_page

            # DataQLD Update
            object_ids.extend(self._create_harvest_objects(pkg_dicts_page, harvest_job))

            if len(pkg_dicts_page) == 0:
                break

            params['start'] = str(int(params['start']) + int(params['rows']))

        return object_ids

    def _create_harvest_objects(self, pkg_dicts, harvest_job):
        # Create harvest objects for each dataset
        object_ids = []
        try:
            package_ids = set()
            for pkg_dict in pkg_dicts:
                if pkg_dict['id'] in package_ids:
                    log.info('Discarding duplicate dataset %s - probably due '
                             'to datasets being changed at the same time as '
                             'when the harvester was paging through',
                             pkg_dict['id'])
                    continue
                package_ids.add(pkg_dict['id'])

                log.debug('Creating HarvestObject for %s %s',
                          pkg_dict['name'], pkg_dict['id'])
                obj = HarvestObject(guid=pkg_dict['id'],
                                    job=harvest_job,
                                    content=json.dumps(pkg_dict))
                obj.save()
                object_ids.append(obj.id)

            return object_ids
        except Exception as e:
            self._save_gather_error('%r' % e.message, harvest_job)


class PlaceholderPlugin(plugins.SingletonPlugin):
    """ Sinkhole for deprecated plugin definitions.
    """
