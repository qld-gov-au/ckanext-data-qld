# encoding: utf-8

import datetime
import re
from six import text_type

from ckan import model
from ckan.lib import uploader
import ckantoolkit as toolkit
from ckantoolkit import c, config, request


def get_user():
    """ Retrieve the current user object.
    """
    # 'g' is not a regular data structure so we can't use 'hasattr'
    if 'userobj' in dir(toolkit.g):
        return toolkit.g.userobj
    else:
        return None


def user_has_admin_access(include_editor_access):
    user = get_user()
    # If user is "None" - they are not logged in.
    if user is None:
        return False
    if user.sysadmin:
        return True

    groups_admin = user.get_groups('organization', 'admin')
    groups_editor = user.get_groups('organization', 'editor') if include_editor_access else []
    groups_list = groups_admin + groups_editor
    organisation_list = [g for g in groups_list if g.type == 'organization']
    return len(organisation_list) > 0


def data_driven_application(data_driven_application):
    """Returns True if data_driven_application value equals yes
        Case insensitive

    :rtype: boolean

    """
    if data_driven_application and data_driven_application.lower() == 'yes':
        return True
    else:
        return False


def dataset_data_driven_application(dataset_id):
    """Returns True if the dataset for dataset_id data_driven_application value equals yes
        Case insensitive

    :rtype: boolean

    """
    try:
        package = toolkit.get_action('package_show')(
            data_dict={'id': dataset_id})
    except toolkit.ObjectNotFound:
        return False

    return data_driven_application(package.get('data_driven_application', ''))


def datarequest_default_organisation():
    """Returns the default organisation for data request from the config file
        Case insensitive.

    :rtype: organisation

    """
    default_organisation = config.get('ckan.datarequests.default_organisation')
    try:
        organisation = toolkit.get_action('organization_show')(
            data_dict={
                'id': default_organisation,
                'include_datasets': False,
                'include_dataset_count': False,
                'include_extras': False,
                'include_users': False,
                'include_groups': False,
                'include_tags': False,
                'include_followers': False
            })
    except toolkit.ObjectNotFound:
        toolkit.abort(404,
                      toolkit._('Default Data Request Organisation not found. Please get the sysadmin to set one up'))

    return organisation


def datarequest_default_organisation_id():
    """Returns the default organisation id for data request from the config file

    :rtype: integer

    """
    organisation_id = datarequest_default_organisation().get('id')
    print('datarequest_default_organisation_id: %s', organisation_id)
    return organisation_id


def datarequest_suggested_description():
    """Returns a datarequest suggested description from admin config

    :rtype: string

    """
    return config.get('ckanext.data_qld.datarequest_suggested_description', '')


# Data.Qld specific comments helper functions

def resource_formats(field):
    """Returns a list of resource formats from admin config

    :rtype: Array resource formats

    """
    resource_formats = config.get('ckanext.data_qld.resource_formats', '').split('\r\n')
    return [{'value': resource_format.strip().upper(), 'label': resource_format.strip().upper()}
            for resource_format in resource_formats]


def profanity_checking_enabled():
    """Check to see if YTP comments extension is enabled and `check_for_profanity` is enabled

    :rtype: bool

    """
    return ytp_comments_enabled() \
        and toolkit.asbool(config.get('ckan.comments.check_for_profanity', False))


def get_request():
    return toolkit.request if hasattr(toolkit.request, 'params') else None


def get_request_action():
    request = get_request()
    return toolkit.get_endpoint()[1] if request else ''


def get_request_path():
    request = get_request()
    return request.path if request else ''


def is_delete_request():
    return get_request_action() == 'delete' or 'package_delete' in get_request_path()


def is_api_request():
    return get_request_action() == 'action' or '/action/' in get_request_path()


def get_gtm_code():
    # To get Google Tag Manager Code
    gtm_code = config.get('ckan.google_tag_manager.gtm_container_id', False)
    return str(gtm_code)


def get_year():
    now = datetime.datetime.now()
    return now.year


def _is_action_configured(name):
    try:
        return toolkit.get_action(name) is not None
    except KeyError:
        return False


def ytp_comments_enabled():
    return _is_action_configured('comment_count')


def is_datarequests_enabled():
    return _is_action_configured('list_datarequests')


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


def is_reporting_enabled():
    return _is_action_configured('report_list')


def is_request_for_resource():
    """
    Searching for a url path for /dataset/ and /resource/
    eg. /dataset/example/resource/b33a702a-f162-44a8-aad9-b9e630a8f56e
    :return:
    """
    original_request = request.environ.get('pylons.original_request')
    if original_request:
        return re.search(r"/dataset/\S+/resource/\S+",
                         original_request.path)
    return False


# this ensures external css/js is loaded from external staging
# if running in cicd/pdev environments.
def set_external_resources():
    environment = config.get('ckan.site_url', '')
    if 'ckan' in environment:
        return '//staging.data.qld.gov.au'
    else:
        return ''


def is_prod():
    environment = config.get('ckan.site_url', '')
    if 'training' in environment:
        return False
    elif 'dev' in environment:
        return False
    elif 'staging' in environment:
        return False
    elif 'ckan' in environment:
        return False
    else:
        return True


def set_background_image_class():
    environment = config.get('ckan.site_url', '')
    if 'training' in environment:
        background_class = 'qg-training'
    elif 'dev' in environment:
        background_class = 'qg-dev'
    elif 'staging' in environment:
        background_class = 'qg-staging'
    elif 'ckan' in environment:
        background_class = 'qg-dev'
    else:
        background_class = ''
    return background_class


def latest_revision(resource_id):
    resource_revisions = model.Session.query(model.resource_revision_table)\
        .filter(model.ResourceRevision.id == resource_id,
                model.ResourceRevision.expired_timestamp > '9999-01-01')
    highest_value = None
    for revision in resource_revisions:
        if highest_value is None or revision.revision_timestamp > \
                highest_value.revision_timestamp:
            highest_value = revision
    return highest_value


def populate_revision(resource):
    if 'revision_timestamp' in resource \
            or toolkit.check_ckan_version(min_version='2.9'):
        return
    current_revision = latest_revision(resource['id'])
    if current_revision is not None:
        resource['revision_timestamp'] = current_revision.revision_timestamp


def unreplied_comments_x_days(thread_url):
    """A helper function for Data.Qld Engagement Reporting
    to highlight un-replied comments after x number of days.
    (Number of days is a constant in the reporting plugin)
    """
    comment_ids = []

    if is_reporting_enabled():
        unreplied_comments = toolkit.get_action(
            'comments_no_replies_after_x_days'
        )({}, {'thread_url': thread_url})

        comment_ids = [comment[1] for comment in unreplied_comments]

    return comment_ids


def get_display_name(user):
    if not isinstance(user, model.User):
        user_name = text_type(user)
        user = model.User.get(user_name)
        if not user:
            return user_name
    return user.display_name


def members_sorted(members):
    '''
    Sorting helper for the members tables
    '''
    members_list = []
    for user_id, user, role in members:
        member_dict = {}
        tag = toolkit.h.linked_user(user_id)
        member_dict['user_id'] = user_id
        member_dict['tag'] = tag
        member_dict['role'] = role
        member_dict['display_name'] = get_display_name(user_id)
        members_list.append(member_dict)

    return sorted(members_list, key=lambda m: m['display_name'].lower())


def get_deletion_reason_template():
    return toolkit.render('package/snippets/deletion_reason.html')


def is_uploaded_file(upload):
    return isinstance(upload, uploader.ALLOWED_UPLOAD_TYPES) and upload.filename


class RequestHelper():
    """ Some useful functions for interacting with the current request.

    Handles both WebOb and Flask request objects.
    """

    def __init__(self, request=None):
        if request:
            self.request = request
        else:
            import ckan.common
            self.request = ckan.common.request

    def get_path(self):
        """ Get the request path, without query string.
        """
        return self.request.path

    def get_method(self):
        """ Get the request method, eg HEAD, GET, POST.
        """
        return self.request.method

    def get_environ(self):
        """ Get the WebOb environment dict.
        """
        return self.request.environ

    def get_cookie(self, field_name, default=None):
        """ Get the value of a cookie, or the default value if not present.
        """
        return self.request.cookies.get(field_name, default)

    def _get_params(self, pylons_attr, flask_attr, field_name=None):
        """ Retrieve a list of all parameters with the specified name
        for the current request.

        If no field name is specified, retrieve the whole parameter object.

        The Flask param attribute will be used if present;
        if not, then the Pylons param attribute will be used.
        """
        if hasattr(self.request, flask_attr):
            param_object = getattr(self.request, flask_attr)
            if field_name:
                return param_object.getlist(field_name)
        else:
            param_object = getattr(self.request, pylons_attr)
            if field_name:
                return param_object.getall(field_name)
        return param_object

    def get_post_params(self, field_name=None):
        """ Retrieve a list of all POST parameters with the specified name
        for the current request.

        If no field name is specified, retrieve the whole parameter object.

        This uses 'request.POST' for Pylons and 'request.form' for Flask.
        """
        return self._get_params('POST', 'form', field_name)

    def get_query_params(self, field_name=None):
        """ Retrieve a list of all GET parameters with the specified name
        for the current request.

        This uses 'request.GET' for Pylons and 'request.args' for Flask.
        """
        return self._get_params('GET', 'args', field_name)

    def delete_param(self, field_name):
        """ Remove the parameter with the specified name from the current
        request. This requires the request parameters to be mutable.
        """
        for collection_name in ['args', 'form', 'GET', 'POST']:
            collection = getattr(self.request, collection_name, {})
            if field_name in collection:
                del collection[field_name]

    def scoped_attrs(self):
        """ Returns a mutable dictionary of attributes that exist in the
        scope of the current request, and will vanish afterward.
        """
        if 'webob.adhoc_attrs' not in self.request.environ:
            self.request.environ['webob.adhoc_attrs'] = {}
        return self.request.environ['webob.adhoc_attrs']

    def get_first_post_param(self, field_name, default=None):
        """ Retrieve the first POST parameter with the specified name
        for the current request.

        This uses 'request.POST' for Pylons and 'request.form' for Flask.
        """
        return self.get_post_params().get(field_name, default)

    def get_first_query_param(self, field_name, default=None):
        """ Retrieve the first GET parameter with the specified name
        for the current request.

        This uses 'request.GET' for Pylons and 'request.args' for Flask.
        """
        return self.get_query_params().get(field_name, default)
