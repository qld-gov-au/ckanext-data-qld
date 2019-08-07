import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import datetime

from ckan.common import c, config
from pylons import request
import re


def get_gtm_code():
    # To get Google Tag Manager Code
    gtm_code = config.get('ckan.google_tag_manager.gtm_container_id', False)
    return str(gtm_code)


def get_year():
    now = datetime.datetime.now()
    return now.year


def ytp_comments_enabled():
    return "ytp_comments" in config.get('ckan.plugins', False)


def get_all_groups():
    groups = toolkit.get_action('group_list')(
        data_dict={'include_dataset_count': False, 'all_fields': True})
    pkg_group_ids = set(group['id'] for group
                        in c.pkg_dict.get('groups', []))
    return [[group['id'], group['display_name']]
            for group in groups if
            group['id'] not in pkg_group_ids]


def get_comment_notification_recipients_enabled():
    return config.get('ckan.comments.follow_mute_enabled', False)


def is_request_for_resource():
    """
    Searching for a url path for /dataset/ and /resource/
    eg. /dataset/test-dataset-name/resource/b33a702a-f162-44a8-aad9-b9e630a8f56e
    :return:
    """
    original_request = request.environ.get('pylons.original_request')
    if original_request:
        return re.search(r"/dataset/\S+/resource/\S+", original_request.path)
    return False


def set_background_image_class():
    environment = config.get('ckan.site_url', '')
    if 'training' in environment:
        background_class = 'qg-training'
    elif 'dev' in environment:
        background_class = 'qg-dev'
    elif 'staging' in environment:
        background_class = 'qg-staging'
    else:
        background_class = ''
    return background_class


class DataQldThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'data_qld_theme')

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'get_gtm_container_id': get_gtm_code,
            'get_year': get_year,
            'ytp_comments_enabled': ytp_comments_enabled,
            'get_all_groups': get_all_groups,
            'is_request_for_resource': is_request_for_resource,
            'set_background_image_class': set_background_image_class,
            'comment_notification_recipients_enabled': get_comment_notification_recipients_enabled
        }
