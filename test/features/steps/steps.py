from behave import step
from behaving.web.steps import *  # noqa: F401, F403
from behaving.personas.steps import *  # noqa: F401, F403
from behaving.web.steps.url import when_i_visit_url
import random


@step('I go to homepage')
def go_to_home(context):
    when_i_visit_url(context, '/')


@step('I log in')
def log_in(context):
    assert context.persona
    context.execute_steps(u"""
        When I go to homepage
        And I click the link with text that contains "Log in"
        And I log in directly
    """)


@step('I log in directly')
def log_in_directly(context):
    """
    This differs to the `log_in` function above by logging in directly to a page where the user login form is presented
    :param context:
    :return:
    """

    assert context.persona
    context.execute_steps(u"""
        When I fill in "login" with "$name"
        And I fill in "password" with "$password"
        And I press the element with xpath "//button[contains(string(), 'Login')]"
        Then I should see an element with xpath "//a[contains(string(), 'Log out')]"
    """)


@step('I fill in title with random text')
def title_random_text(context):

    assert context.persona
    context.execute_steps(u"""
        When I fill in "title" with "Test Title {0}"
    """.format(random.randrange(1000)))


@step('I log in and go to datarequest page')
def log_in_go_to_datarequest_page(context):
    assert context.persona
    context.execute_steps(u"""
        When I log in
        And I go to datarequest page
    """)


@step('I go to datarequest page')
def go_to_datarequest_page(context):
    when_i_visit_url(context, '/datarequest')


@step('I log in and create a datarequest')
def log_in_create_a_datarequest(context):

    assert context.persona
    context.execute_steps(u"""
        When I log in and go to datarequest page
        And I create a datarequest
    """)


@step('I create a datarequest')
def create_datarequest(context):

    assert context.persona
    context.execute_steps(u"""
        When I go to datarequest page
        And I click the link with text that contains "Add data request"
        And I fill in title with random text
        And I fill in "description" with "Test description"
        And I press the element with xpath "//button[contains(string(), 'Create data request')]"
    """)


@step('I go to my reports page')
def go_to_reporting_page(context):
    when_i_visit_url(context, '/dashboard/reporting')


@step(u'I go to dataset "{name}"')
def go_to_dataset(context, name):
    when_i_visit_url(context, '/dataset/' + name)


@step(u'I go to dataset "{name}" comments')
def go_to_dataset_comments(context, name):
    context.execute_steps(u"""
        When I go to dataset "%s"
        And I click the link with text that contains "Comments"
    """ % (name))


@step(u'I submit a comment with subject "{subject}" and comment "{comment}"')
def submit_comment_with_subject_and_comment(context, subject, comment):
    """
    There can be multiple comment forms per page (add, edit, reply) each with fields named "subject" and "comment"
    This step overcomes a limitation of the fill() method which only fills a form field by name
    :param context:
    :param subject:
    :param comment:
    :return:
    """
    context.browser.execute_script(
        "document.querySelector('form#comment_form input[name=\"subject\"]').value = '%s';" % subject)
    context.browser.execute_script(
        "document.querySelector('form#comment_form textarea[name=\"comment\"]').value = '%s';" % comment)
    context.browser.execute_script(
        "document.querySelector('form#comment_form .form-actions input[type=\"submit\"]').click();")


@step('I create a dataset with license {license} and resource file {file}')
def create_dataset(context, license, file):
    assert context.persona
    context.execute_steps(u"""
        When I visit "dataset/new"
        And I fill in title with random text
        And I fill in "notes" with "Description"
        And I fill in "version" with "1.0"
        And I fill in "author_email" with "test@me.com"
        And I execute the script "document.getElementById('field-license_id').value={license}"
        And I press "Add Data"
        And I attach the file {file} to "upload"
        And I fill in "name" with "Test Resource"
        And I execute the script "document.getElementById('field-format').value='JSON'"
        And I fill in "description" with "Test Resource Description"
        And I press "Finish"
    """.format(license=license, file=file))
