import json

import pytest

from ckan.tests import factories
from ckan.lib.helpers import url_for

import ckanext.resource_visibility.constants as const

from ckanext.data_qld.helpers import is_ckan_29


@pytest.fixture
def pkg_show_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="package_show",
                  ver=3)
    assert url == "/api/3/action/package_show"
    return url


@pytest.fixture
def pkg_update_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="package_update",
                  ver=3)
    assert url == "/api/3/action/package_update"
    return url


@pytest.fixture
def pkg_patch_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="package_patch",
                  ver=3)
    assert url == "/api/3/action/package_patch"
    return url


@pytest.fixture
def res_create_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="resource_create",
                  ver=3)
    assert url == "/api/3/action/resource_create"
    return url


@pytest.fixture
def res_patch_url():
    url = url_for(controller='api',
                  action="action",
                  logic_function="resource_patch",
                  ver=3)
    assert url == "/api/3/action/resource_patch"
    return url


def _get_resource_read_url(package_id, resource_id):
    controller = "resource" if is_ckan_29() else "package"
    action = "read" if is_ckan_29() else "resource_read"

    return url_for(controller=controller,
                   action=action,
                   id=package_id,
                   resource_id=resource_id)


def _get_pkg_dict(app, url, package_id, user=None):
    response = app.get(
        url=url,
        params={"name_or_id": package_id},
        status=200,
        extra_environ={"REMOTE_USER": str(user["name"]) if user else ""},
    )

    return response.json['result']


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context", "mock_storage")
class TestApiPrivacyAssessment:
    """privacy_assessment_result must be visible via API only for organization
    editors, admins and sysadmins.
    """

    def test_excluded_for_anon(self, dataset_factory, resource_factory, app,
                               pkg_show_url):

        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": ""})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_ASSESS_RESULT not in resource

    def test_excluded_for_regular_user(self, dataset_factory, resource_factory,
                                       app, pkg_show_url):
        user = factories.User()
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": str(user["name"])})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_ASSESS_RESULT not in resource

    def test_excluded_for_member(self, dataset_factory, resource_factory, app,
                                 pkg_show_url):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["name"],
            "capacity": "member"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"])

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": str(user['name'])})

        resource = response.json['result']['resources'][0]

        assert const.FIELD_ASSESS_RESULT not in resource

    def test_present_for_editor_and_admin(self, dataset_factory,
                                          resource_factory, app, pkg_show_url):
        user1 = factories.User()
        user2 = factories.User()
        org = factories.Organization(users=[{
            "name": user1["name"],
            "capacity": "editor"
        }, {
            "name": user2["name"],
            "capacity": "admin"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"])

        for user in [user1, user2]:
            response = app.get(
                url=pkg_show_url,
                params={"name_or_id": dataset["id"]},
                status=200,
                extra_environ={"REMOTE_USER": str(user['name'])})
            resource = response.json['result']['resources'][0]

            assert const.FIELD_ASSESS_RESULT in resource

    def test_present_for_sysadmin(self, dataset_factory, resource_factory, app,
                                  pkg_show_url, sysadmin):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        response = app.get(
            url=pkg_show_url,
            params={"name_or_id": dataset["id"]},
            status=200,
            extra_environ={"REMOTE_USER": str(sysadmin['name'])})
        resource = response.json['result']['resources'][0]

        assert const.FIELD_ASSESS_RESULT in resource


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context", "mock_storage")
class TestResourceVisibility:
    """We have a custom logic for resource visibility

    False - HIDE
    True - SHOW

    if resource_visible == c.FALSE:
        return False

    if gov_acknowledgement == c.YES:
        if request_privacy_assess == c.NO or not request_privacy_assess:
            return True
        if request_privacy_assess == c.YES:
            if de_identified_data == c.NO:
                return True
            elif de_identified_data == c.YES:
                return False
    elif gov_acknowledgement == c.NO:
        return de_identified_data == c.NO


    dataset_factory creates a dataset with 1 resource, if you want to create
    a dataset without resources - pass resource=[] as arg

    """

    def test_excluded_for_anon(self, app, dataset_factory, resource_factory,
                               pkg_show_url):

        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"])

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": ""})
        pkg_dict = response.json['result']

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

    def test_not_excluded_for_anon_not_de_identified(self, dataset_factory,
                                                     resource_factory, app,
                                                     pkg_show_url):

        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": ""})
        pkg_dict = response.json['result']

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

    def test_excluded_for_regular_user(self, dataset_factory, app,
                                       pkg_show_url):
        user = factories.User()
        dataset = dataset_factory()

        response = app.get(url=pkg_show_url,
                           params={"name_or_id": dataset["id"]},
                           status=200,
                           extra_environ={"REMOTE_USER": str(user["name"])})
        pkg_dict = response.json['result']

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

    def test_resource_page_not_accessible_for_regular_user_if_hidden(
            self, app, dataset_factory, resource_factory):
        user = factories.User()

        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"],
                                    resource_visible="FALSE")

        app.get(url=_get_resource_read_url(dataset['id'], resource['id']),
                status=404,
                extra_environ={"REMOTE_USER": str(user["name"])})

    def test_visible_for_editor_or_admin(self, dataset_factory, app,
                                         pkg_show_url, resource_factory):
        user1 = factories.User()
        user2 = factories.User()
        org = factories.Organization(users=[{
            "name": user1["name"],
            "capacity": "editor"
        }, {
            "name": user2["name"],
            "capacity": "admin"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        for user in [user1, user2]:
            response = app.get(
                url=pkg_show_url,
                params={"name_or_id": dataset["id"]},
                status=200,
                extra_environ={"REMOTE_USER": str(user['name'])})
            pkg_dict = response.json['result']

            assert len(pkg_dict["resources"]) == 1
            assert pkg_dict["num_resources"] == 1

    def test_visible_for_sysadmin(self, dataset_factory, resource_factory, app,
                                  pkg_show_url, sysadmin):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        response = app.get(
            url=pkg_show_url,
            params={"name_or_id": dataset["id"]},
            status=200,
            extra_environ={"REMOTE_USER": str(sysadmin['name'])})
        pkg_dict = response.json['result']

        assert len(pkg_dict["resources"]) == 2
        assert pkg_dict["num_resources"] == 2

    def test_regular_user_different_conditions(self, dataset_factory,
                                               resource_factory, app,
                                               pkg_show_url):
        user = factories.User()

        # not resource_visible -> HIDE
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

        # resource_visible & not governance_acknowledgement & not de_identified_data -> SHOW
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="NO")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & not governance_acknowledgement & de_identified_data -> HIDE
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="NO")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

        # resource_visible & governance_acknowledgement & not request_privacy_assessment -> SHOW
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES",
                         request_privacy_assessment="NO")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & governance_acknowledgement & NONE request_privacy_assessment -> SHOW
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & governance_acknowledgement & request_privacy_assessment & de_identified_data -> HIDE
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES",
                         request_privacy_assessment="YES")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

        # resource_visible & governance_acknowledgement & request_privacy_assessment & not de_identified_data -> SHOW
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES",
                         request_privacy_assessment="YES")

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context", "mock_storage")
class TestSchemaAlignment:

    def test_update_and_patch_default_schema(self, dataset_factory, app,
                                             pkg_show_url, pkg_update_url,
                                             pkg_patch_url, resource_factory):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["name"],
            "capacity": "editor"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        new_schema = {
            "fields": [{
                "name": "x",
                "title": "New schema",
                "type": "integer"
            }],
            "primaryKey": "x"
        }

        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)
        pkg_dict['default_data_schema'] = new_schema

        resp = app.post(pkg_update_url,
                        params=json.dumps(pkg_dict),
                        extra_environ={"REMOTE_USER": str(user['name'])})
        assert resp.json['result']['default_data_schema'] == new_schema

        app.post(pkg_patch_url,
                 params=json.dumps({
                     "id": dataset["id"],
                     "default_data_schema": ""
                 }),
                 extra_environ={"REMOTE_USER": str(user['name'])})
        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert not pkg_dict['default_data_schema']

    def test_create_resource_with_custom_schema(self, dataset_factory,
                                                resource_factory):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["name"],
            "capacity": "editor"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        schema = {
            "fields": [{
                "format": "default",
                "name": "Game Number",
                "type": "integer"
            }, {
                "format": "default",
                "name": "Game Length",
                "type": "integer"
            }],
            "missingValues": [""]
        }

        resource = resource_factory(package_id=dataset["id"], schema=schema)

        assert resource['schema'] == schema

    def test_align_default_schema_visible_via_api(self, dataset_factory,
                                                  resource_factory, app,
                                                  pkg_show_url):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        user = factories.User()
        pkg_dict = _get_pkg_dict(app, pkg_show_url, dataset["id"], user)

        assert 'align_default_schema' in pkg_dict['resources'][0]

    def test_updating_align_default_schema_via_api_is_forbidden(
            self, dataset_factory, resource_factory, app, res_patch_url):

        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["name"],
            "capacity": "editor"
        }])
        dataset = dataset_factory(owner_org=org["id"])
        resource = resource_factory(package_id=dataset["id"])

        resp = app.post(res_patch_url,
                        params=json.dumps({
                            "id": resource["id"],
                            "align_default_schema": 1
                        }),
                        status=409,
                        extra_environ={"REMOTE_USER": str(user['name'])})

        assert not resp.json['success']
        assert 'This field couldn\'t be updated via API' in resp.json['error'][
            'align_default_schema']
