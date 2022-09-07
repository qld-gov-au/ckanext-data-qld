from ckan.tests import factories
import pytest

from ckan.lib.helpers import url_for

import ckanext.resource_visibility.constants as const


@pytest.fixture
def package_show_api_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="package_show",
                  ver=3)
    assert url == "/api/3/action/package_show"
    return url


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context")
class TestApiPrivacyAssessment:
    """privacy_assessment_result must be visible via API only for organization
    editors, admins and sysadmins.
    """
    def test_excluded_for_anon(self, dataset_factory, resource_factory, app,
                               package_show_api_url):

        dataset = dataset_factory(de_identified_data="NO")
        resource_factory(package_id=dataset["id"])

        response = app.get(url=package_show_api_url,
                           query_string={"name_or_id": dataset["id"]},
                           status=200,
                           environ_overrides={"REMOTE_USER": u""})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_PRIVACY_ASSESS_RESULT not in resource

    def test_excluded_for_regular_user(self, dataset_factory, resource_factory,
                                       app, package_show_api_url):
        user = factories.User()
        dataset = dataset_factory(de_identified_data="NO")
        resource_factory(package_id=dataset["id"])

        response = app.get(url=package_show_api_url,
                           query_string={"name_or_id": dataset["id"]},
                           status=200,
                           environ_overrides={"REMOTE_USER": user["name"]})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_PRIVACY_ASSESS_RESULT not in resource

    def test_excluded_for_member(self, dataset_factory, resource_factory, app,
                                 package_show_api_url):
        user = factories.User()
        org = factories.Organization(users=[{"name": user["name"],"capacity": "member"}])

        dataset = dataset_factory(de_identified_data="NO", owner_org=org["id"])
        resource_factory(package_id=dataset["id"])

        response = app.get(url=package_show_api_url,
                           query_string={"name_or_id": dataset["id"]},
                           status=200,
                           environ_overrides={"REMOTE_USER": user['name']})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_PRIVACY_ASSESS_RESULT not in resource

    def test_present_for_editor_and_admin(self, dataset_factory,
                                          resource_factory, app,
                                          package_show_api_url):
        user1 = factories.User()
        user2 = factories.User()
        org = factories.Organization(users=[
            {"name": user1["name"], "capacity": "editor"},
            {"name": user2["name"], "capacity": "admin"}]
        )

        dataset = dataset_factory(de_identified_data="NO", owner_org=org["id"])
        resource_factory(package_id=dataset["id"])

        for user in [user1, user2]:
            response = app.get(url=package_show_api_url,
                               query_string={"name_or_id": dataset["id"]},
                               status=200,
                               environ_overrides={"REMOTE_USER": user['name']})
            resource = response.json['result']['resources'][0]

            assert const.FIELD_PRIVACY_ASSESS_RESULT in resource

    def test_present_for_sysadmin(self, dataset_factory, resource_factory, app,
                                  package_show_api_url, sysadmin):
        dataset = dataset_factory(de_identified_data="NO")
        resource_factory(package_id=dataset["id"])

        response = app.get(url=package_show_api_url,
                           query_string={"name_or_id": dataset["id"]},
                           status=200,
                           environ_overrides={"REMOTE_USER": sysadmin['name']})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_PRIVACY_ASSESS_RESULT in resource
