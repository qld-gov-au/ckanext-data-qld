# encoding: utf-8

import logging

import ckantoolkit as tk
from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters.ckanharvester import ContentFetchError, SearchError
from ckan import model
from ckan.lib.helpers import json

import six
from six.moves.urllib.parse import urlencode
import datetime

log = logging.getLogger(__name__)


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
        except SearchError:
            log.info('Searching for datasets changed since last time '
                     'gave an error', exc_info=True)
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
            log.info('Searching for all datasets gave an error: %s', exc_info=True)
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
