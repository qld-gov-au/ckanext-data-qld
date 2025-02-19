# encoding: utf-8

import pytest

from ckan import model
from ckan.tests import factories
from ckan.tests.helpers import call_action
import ckantoolkit as tk

from ckanext.resource_visibility import constants as const

from ckanext.data_qld.tests.conftest import _get_resource_schema
from ckanext.data_qld.constants import FIELD_ALIGNMENT, FIELD_DEFAULT_SCHEMA


def _make_context(user=None):
    if user:
        return {"user": user['name'], "auth_user_obj": model.User.get(user["name"])}
    else:
        return {"user": "", "auth_user_obj": model.AnonymousUser()}


def _get_pkg_dict(package_id, user=None):
    return tk.get_action('package_show')(
        context=_make_context(user), data_dict={"id": package_id}
    )


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context",
                         "mock_storage")
class TestApiPrivacyAssessment:
    """privacy_assessment_result and `request_privacy_assessment` field
    must be visible via API only for organization editors, admins and sysadmins.
    """

    def test_excluded_for_anon(self, dataset_factory, resource_factory):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        pkg_dict = _get_pkg_dict(dataset['id'])
        resource = pkg_dict['resources'][0]

        assert const.FIELD_REQUEST_ASSESS not in resource
        assert const.FIELD_ASSESS_RESULT not in resource

    def test_excluded_for_regular_user(self, dataset_factory, resource_factory):
        user = factories.User()
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        pkg_dict = _get_pkg_dict(dataset['id'], user)
        resource = pkg_dict['resources'][0]

        assert const.FIELD_REQUEST_ASSESS not in resource
        assert const.FIELD_ASSESS_RESULT not in resource

    def test_excluded_for_member(self, dataset_factory, resource_factory):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["id"],
            "capacity": "member"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        resource = pkg_dict['resources'][0]

        assert const.FIELD_REQUEST_ASSESS not in resource
        assert const.FIELD_ASSESS_RESULT not in resource

    def test_excluded_for_editor_and_admin_of_another_org(
            self, dataset_factory, resource_factory):
        """An editor or administrator of an organization must have a special
        permission only within that organization and not in others."""
        user1 = factories.User()
        user2 = factories.User()
        factories.Organization(users=[{
            "name": user1["id"],
            "capacity": "editor"
        }, {
            "name": user2["name"],
            "capacity": "admin"
        }])

        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        for user in [user1, user2]:
            pkg_dict = _get_pkg_dict(dataset['id'], user)
            resource = pkg_dict['resources'][0]

            assert const.FIELD_REQUEST_ASSESS not in resource
            assert const.FIELD_ASSESS_RESULT not in resource

    def test_present_for_editor_and_admin(self, dataset_factory, resource_factory):
        user1 = factories.User()
        user2 = factories.User()
        org = factories.Organization(users=[{
            "name": user1["id"],
            "capacity": "editor"
        }, {
            "name": user2["id"],
            "capacity": "admin"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        for user in [user1, user2]:
            pkg_dict = _get_pkg_dict(dataset['id'], user)
            resource = pkg_dict['resources'][0]

            assert const.FIELD_REQUEST_ASSESS in resource
            assert const.FIELD_ASSESS_RESULT in resource

    def test_present_for_sysadmin(self, dataset_factory, resource_factory):
        sysadmin = factories.Sysadmin()
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment=const.YES)

        pkg_dict = _get_pkg_dict(dataset['id'], sysadmin)
        resource = pkg_dict['resources'][0]

        assert const.FIELD_REQUEST_ASSESS in resource
        assert const.FIELD_ASSESS_RESULT in resource


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context",
                         "mock_storage")
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

    def test_excluded_for_anon(self, dataset_factory, resource_factory):
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"])

        pkg_dict = _get_pkg_dict(dataset['id'])

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

    def test_not_excluded_for_anon_not_de_identified(self, dataset_factory,
                                                     resource_factory):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        pkg_dict = _get_pkg_dict(dataset['id'])

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

    def test_excluded_for_regular_user(self, dataset_factory):
        user = factories.User()
        dataset = dataset_factory()

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

    def test_resource_page_not_accessible_for_regular_user_if_hidden(
            self, dataset_factory, resource_factory):
        user = factories.User()
        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"],
                                    resource_visible="FALSE")

        with pytest.raises(tk.ObjectNotFound):
            tk.get_action('resource_show')(
                context=_make_context(user),
                data_dict={"id": resource['id']}
            )

    def test_visible_for_editor_or_admin(self, dataset_factory, resource_factory):
        user1 = factories.User()
        user2 = factories.User()
        org = factories.Organization(users=[{
            "name": user1["id"],
            "capacity": "editor"
        }, {
            "name": user2["id"],
            "capacity": "admin"
        }])

        dataset = dataset_factory(owner_org=org["id"])
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        for user in [user1, user2]:
            pkg_dict = _get_pkg_dict(dataset['id'], user)

            assert len(pkg_dict["resources"]) == 1
            assert pkg_dict["num_resources"] == 1

    def test_visible_for_sysadmin(self, dataset_factory, resource_factory):
        sysadmin = factories.Sysadmin()
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        pkg_dict = _get_pkg_dict(dataset['id'], sysadmin)

        assert len(pkg_dict["resources"]) == 2
        assert pkg_dict["num_resources"] == 2

    def test_regular_user_different_conditions(self, dataset_factory,
                                               resource_factory):
        user = factories.User()
        # not resource_visible -> HIDE
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"], resource_visible="FALSE")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

        # resource_visible & not governance_acknowledgement & not de_identified_data -> SHOW
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="NO")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & not governance_acknowledgement & de_identified_data -> HIDE
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="NO")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0

        # resource_visible & governance_acknowledgement & not request_privacy_assessment -> SHOW
        dataset = dataset_factory(de_identified_data="YES")
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES",
                         request_privacy_assessment="NO")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & governance_acknowledgement & NONE request_privacy_assessment -> SHOW
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 1

        # resource_visible & governance_acknowledgement & request_privacy_assessment -> HIDE
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         resource_visible="TRUE",
                         governance_acknowledgement="YES",
                         request_privacy_assessment="YES")

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert not pkg_dict["resources"]
        assert pkg_dict["num_resources"] == 0


@pytest.mark.usefixtures("with_plugins", "with_request_context",
                         "mock_storage")
class TestSchemaAlignment:

    def test_update_and_patch_default_schema(self, dataset_factory,
                                             resource_factory):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["id"],
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

        pkg_dict = _get_pkg_dict(dataset['id'], user)
        pkg_dict['default_data_schema'] = new_schema

        context = _make_context(user)
        resp = call_action('package_update', context=context, **pkg_dict)
        assert resp['default_data_schema'] == new_schema

        call_action("package_patch", context=context,
                    id=dataset["id"], default_data_schema="")
        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert 'default_data_schema' not in pkg_dict

    def test_create_resource_with_custom_schema(self, dataset_factory,
                                                resource_factory):
        user = factories.User()
        org = factories.Organization(users=[{
            "name": user["id"],
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
                                                  resource_factory):
        user = factories.User()
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"])

        pkg_dict = _get_pkg_dict(dataset['id'], user)

        assert FIELD_ALIGNMENT in pkg_dict['resources'][0]


@pytest.mark.usefixtures("with_plugins", "clean_db", "with_request_context",
                         "mock_storage")
class TestDefaultSchemaAlignment:

    def test_update_default_schema_triggers_alignment_check(
            self, dataset_factory, resource_factory):
        """Update of a default_schema must trigger check of schemas alignment"""
        user = factories.User()
        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"])

        assert not resource[FIELD_ALIGNMENT]

        call_action("package_patch",
                    {"user": user['name']},
                    id=dataset["id"],
                    default_data_schema=_get_resource_schema())

        resource = call_action("resource_show", id=resource["id"])
        assert resource[FIELD_ALIGNMENT]

    def test_set_empty_default_schema(self, dataset_factory, resource_factory):
        schema = _get_resource_schema()
        user = factories.User()
        dataset = dataset_factory(**{FIELD_DEFAULT_SCHEMA: schema})
        resource = resource_factory(package_id=dataset["id"])

        assert resource[FIELD_ALIGNMENT]

        call_action("package_patch", {"user": user['name']},
                    id=dataset["id"], default_data_schema="")

        resource = call_action("resource_show", id=resource["id"])
        assert not resource[FIELD_ALIGNMENT]
