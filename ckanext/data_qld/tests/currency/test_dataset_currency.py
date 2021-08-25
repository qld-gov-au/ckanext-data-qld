# encoding: utf-8

import datetime
from bs4 import BeautifulSoup
from nose.tools import (
    assert_equal,
    assert_not_equal,
    assert_raises,
    assert_true,
    assert_in
)

from mock import patch, MagicMock
from ckan.lib.helpers import url_for

import ckan.model as model
import ckan.plugins as p
from ckan.lib import search

import ckan.tests.helpers as helpers
import ckan.tests.factories as factories

webtest_submit = helpers.webtest_submit
submit_and_follow = helpers.submit_and_follow

UPDATE_FREQUENCY = ['annually', 'semiannually', 'quarterly', 'monthly']


def _get_package_new_page(app):
    user = factories.User()
    env = {'REMOTE_USER': user['name'].encode('ascii')}
    response = app.get(
        url=url_for(controller='package', action='new'),
        extra_environ=env,
    )
    return env, response


class TestPackageNew(helpers.FunctionalTestBase):
    def test_form_renders(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        assert_true('dataset-edit' in response.forms)

    def test_package_due_date(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        form = response.forms['dataset-edit']

        for update_frequency in UPDATE_FREQUENCY:
            form['field-update_frequency'] = update_frequency
            assert 'field-next_update_due' in form.fields

    def test_package_due_date_monthly(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        form = response.forms['dataset-edit']

        form['field-update_frequency'] = 'monthly'
        form['field-next_update_due'] = datetime.datetime.now() + 29

        form = response.forms['dataset-edit']
        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        assert_in('The form contains invalid entries', response.body)

        assert_in('Next Update due : Must be one month from now', response.body)

    def test_package_due_date_quarterly(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        form = response.forms['dataset-edit']

        form['field-update_frequency'] = 'quarterly'
        form['field-next_update_due'] = datetime.datetime.now() + 90

        form = response.forms['dataset-edit']
        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        assert_in('The form contains invalid entries', response.body)

        assert_in('Next Update due : Must be on 91 days from now', response.body)

    def test_package_due_date_semiannually(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        form = response.forms['dataset-edit']

        form['field-update_frequency'] = 'monthly'
        form['field-next_update_due'] = datetime.datetime.now() + 181

        form = response.forms['dataset-edit']
        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        assert_in('The form contains invalid entries', response.body)

        assert_in('Next Update due : Must be on 182 days from now', response.body)

    def test_package_due_date_annually(self):
        app = self._get_test_app()
        env, response = _get_package_new_page(app)
        form = response.forms['dataset-edit']

        form['field-update_frequency'] = 'monthly'
        form['field-next_update_due'] = datetime.datetime.now() + 364

        response = webtest_submit(form, 'save', status=200, extra_environ=env)
        assert_in('The form contains invalid entries', response.body)

        assert_in('Next Update due : Must be on 365 days from now', response.body)
