import os
import json

from behave import fixture, use_fixture
from behaving import environment as benv
from behaving.web.steps.browser import named_browser


# Path to the root of the project.
ROOT_PATH = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    '../../'))

# Base URL for relative paths resolution.
BASE_URL = 'http://ckan:3000/'

# URL of remote Chrome instance.
REMOTE_CHROME_URL = 'http://chrome:4444/wd/hub'

# @see .docker/scripts/init.sh for credentials.
PERSONAS = {
    'SysAdmin': {
        'name': u'admin',
        'email': u'admin@localhost',
        'password': u'Password123!'
    },
    'Unauthenticated': {
        'name': u'',
        'email': u'',
        'password': u''
    },
    'Organisation Admin': {
        'name': u'organisation_admin',
        'email': u'organisation_admin@localhost',
        'password': u'Password123!'
    },
    'Group Admin': {
        'name': u'group_admin',
        'email': u'group_admin@localhost',
        'password': u'Password123!'
    },
    'Publisher': {
        'name': u'editor',
        'email': u'publisher@localhost',
        'password': u'Password123!'
    },
    'Walker': {
        'name': u'walker',
        'email': u'walker@localhost',
        'password': u'Password123!'
    },
    'Foodie': {
        'name': u'foodie',
        'email': u'foodie@localhost',
        'password': u'Password123!'
    },
    # This user will not be assigned to any organisations
    'CKANUser': {
        'name': u'ckan_user',
        'email': u'ckan_user@localhost',
        'password': u'Password123!'
    },
    'TestOrgAdmin': {
        'name': u'test_org_admin',
        'email': u'test_org_admin@localhost',
        'password': u'Password123!'
    },
    'TestOrgEditor': {
        'name': u'test_org_editor',
        'email': u'test_org_editor@localhost',
        'password': u'Password123!'
    },
    'TestOrgMember': {
        'name': u'test_org_member',
        'email': u'test_org_member@localhost',
        'password': u'Password123!'
    },
    'DataRequestOrgAdmin': {
        'name': u'dr_admin',
        'email': u'dr_admin@localhost',
        'password': u'Password123!'
    },
    'DataRequestOrgEditor': {
        'name': u'dr_editor',
        'email': u'dr_editor@localhost',
        'password': u'Password123!'
    },
    'DataRequestOrgMember': {
        'name': u'dr_member',
        'email': u'dr_member@localhost',
        'password': u'Password123!'
    },
    'ReportingOrgAdmin': {
        'name': u'report_admin',
        'email': u'report_admin@localhost',
        'password': u'Password123!'
    },
    'ReportingOrgEditor': {
        'name': u'report_editor',
        'email': u'report_editor@localhost',
        'password': u'Password123!'
    }
}


def before_all(context):
    # The path where screenshots will be saved.
    context.screenshots_dir = os.path.join(ROOT_PATH, 'test/screenshots')
    # The path where file attachments can be found.
    context.attachment_dir = os.path.join(ROOT_PATH, 'test/fixtures')
    # The path where emails can be found.
    context.mail_path = os.path.join(ROOT_PATH, 'test/emails')

    # Set base url for all relative links.
    context.base_url = BASE_URL

    # Always use remote web driver.
    context.remote_webdriver = 1
    context.default_browser = 'chrome'
    context.browser_args = {'command_executor': REMOTE_CHROME_URL}

    # Set the rest of the settings to default Behaving's settings.
    benv.before_all(context)


def after_all(context):
    benv.after_all(context)


def before_feature(context, feature):
    benv.before_feature(context, feature)


def after_feature(context, feature):
    benv.after_feature(context, feature)


def before_scenario(context, scenario):
    benv.before_scenario(context, scenario)
    # Always use remote browser.
    named_browser(context, 'remote')
    # Set personas.
    context.personas = PERSONAS


def after_scenario(context, scenario):
    benv.after_scenario(context, scenario)


def before_tag(context, tag):
    """Parse scenario tag to call the appropriate fixture

    Args:
        tag (str): tag string
    """
    FIXTURE_NAME = 0
    PARAMS = slice(1, None)

    # fixture_name = fixture.dataset_with_schema
    # params = name=package-with-schema
    parts = tag.split(":")

    if parts[FIXTURE_NAME].startswith("fixture.dataset_with_schema"):
        use_fixture(dataset_with_schema, context, *parts[PARAMS])


@fixture
def dataset_with_schema(context, path="", **kwargs):
    context.execute_steps(u"""
        Given browser "remote"
        Then I visit "api/action/qld_test_create_dataset?{}"
    """.format(path))

    json_content = context.browser.find_by_tag("pre")[0].text
    pkg_data = json.loads(json_content)['result']
    pkg_id = pkg_data['id']
    context.dataset = pkg_data

    yield

    context.execute_steps(u"""
        Given browser "remote"
        Then I visit "api/action/qld_test_purge_dataset?id={}"
    """.format(pkg_id))

    context.browser.quit()
