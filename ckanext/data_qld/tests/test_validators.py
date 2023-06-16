import pytest

import ckan.lib.navl.dictization_functions as df
import ckan.model as model

from ckanext.resource_visibility.validators import privacy_assessment_result


def _make_context():
    return {"model": model, "session": model.Session}


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context", "mock_storage",
                         "do_not_validate")
class TestPrivacyAssessmentResultValidator:
    '''
    Test that only sysadmin is able to edit a resource
    '''

    def test_non_sysadmins_restricted_to_edit(self, user, dataset_factory,
                                              resource_factory):
        context = _make_context()
        context['user'] = user['name']

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"],
                                    privacy_assessment_result="initial value")

        value = 'new value'
        key = (u'resources', 0, u'privacy_assessment_result')
        res_id = (u'resources', 0, u'id')

        data = {key: value, res_id: resource["id"]}

        errors = {key: []}

        with pytest.raises(df.StopOnError):
            privacy_assessment_result(key, data, errors, context)

        assert "You are not allowed to edit this field." in errors[key]

    def test_non_sysadmins_restricted_to_edit_if_value_didnt_change(
            self, user, dataset_factory, resource_factory):
        context = _make_context()
        context['user'] = user['name']

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"],
                                    privacy_assessment_result="initial value")

        value = 'initial value'
        key = (u'resources', 0, u'privacy_assessment_result')
        res_id = (u'resources', 0, u'id')

        errors = {key: []}

        data = {key: value, res_id: resource["id"]}

        privacy_assessment_result(key, data, errors, context)

    def test_non_sysadmins_cannot_empty_field(self, user, dataset_factory,
                                              resource_factory):
        context = _make_context()
        context['user'] = user['name']

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"],
                                    privacy_assessment_result="initial value")

        value = ''
        key = (u'resources', 0, u'privacy_assessment_result')
        res_id = (u'resources', 0, u'id')

        errors = {key: []}

        data = {key: value, res_id: resource["id"]}

        with pytest.raises(df.StopOnError):
            privacy_assessment_result(key, data, errors, context)

        assert "You are not allowed to edit this field." in errors[key]

    def test_sysadmins_allowed(self, sysadmin, dataset_factory,
                               resource_factory):
        context = _make_context()
        context['user'] = sysadmin['name']

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"])

        value = 'Data'
        key = (u'resources', 0, u'privacy_assessment_result')
        res_id = (u'resources', 0, u'id')

        data = {key: value, res_id: resource["id"]}

        errors = {key: []}

        privacy_assessment_result(key, data, errors, context)

    def test_ignore_auth(self, dataset_factory, resource_factory):
        context = _make_context()
        context['ignore_auth'] = True

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"])

        value = 'Data'
        key = (u'resources', 0, u'privacy_assessment_result')
        res_id = (u'resources', 0, u'id')

        data = {key: value, res_id: resource["id"]}

        errors = {key: []}

        privacy_assessment_result(key, data, errors, context)
