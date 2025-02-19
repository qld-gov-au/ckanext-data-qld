import pytest

import ckan.model as model
import ckantoolkit as tk
from ckan.tests import factories
from ckan.tests.helpers import call_action

from ckanext.data_qld.reporting.helpers import helpers


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db",
                         "mock_storage", "do_not_validate")
class TestAdminReportDeIdentifiedNoSchema:

    def test_with_package(self, dataset_factory, resource_factory):
        dataset = dataset_factory(default_data_schema="",
                                  de_identified_data="YES")
        resource_factory(package_id=dataset["id"])
        call_action("package_patch",
                    context=_make_context(),
                    id=dataset["id"],
                    notes="test")

        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              org_id=dataset["owner_org"],
                              count_from="2011-01-01",
                              return_count_only=True)

        assert counter == 1

    def test_without_packages(self):
        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              org_id=factories.Organization()["id"],
                              count_from="2011-01-01",
                              return_count_only=True)

        assert counter == 0

    def test_with_count_from_in_future(self, dataset_factory,
                                       resource_factory):
        dataset = dataset_factory(default_data_schema="")
        resource_factory(package_id=dataset["id"])

        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              org_id=factories.Organization()["id"],
                              count_from="2045-01-01",
                              return_count_only=True)

        assert counter == 0

    def test_with_multiple_packages(self, dataset_factory, resource_factory):
        org_id = factories.Organization()["id"]

        for _ in range(3):
            dataset = dataset_factory(default_data_schema="",
                                      owner_org=org_id,
                                      de_identified_data="YES")
            resource_factory(package_id=dataset["id"])
            call_action("package_patch",
                        context=_make_context(),
                        id=dataset["id"],
                        notes="test")

        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              org_id=org_id,
                              count_from="2011-01-01",
                              return_count_only=True)

        assert counter == 3

    def test_without_org_id(self, dataset_factory, resource_factory):
        dataset = dataset_factory(default_data_schema="")
        resource_factory(package_id=dataset["id"])

        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              count_from="2011-01-01",
                              return_count_only=True)

        assert counter == 0

    def test_dataset_without_resource_has_no_next_update_due(
            self, dataset_factory):
        dataset = dataset_factory(default_data_schema="")

        counter = call_action("de_identified_datasets_no_schema",
                              _make_context(),
                              org_id=dataset["owner_org"],
                              count_from="2011-01-01",
                              return_count_only=True)

        assert counter == 0


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db",
                         "mock_storage", "do_not_validate")
class TestAdminReportCSVExport:

    def test_as_regular_user(self, app, user):
        app.get('/', extra_environ={"REMOTE_USER": str(user["name"])})
        org_id = factories.Organization()["id"]

        with pytest.raises(tk.NotAuthorized):
            helpers.gather_admin_metrics(org_id, "admin")

    def test_as_sysadmin(self, app, dataset_factory, resource_factory,
                         sysadmin):
        app.get('/', extra_environ={"REMOTE_USER": str(sysadmin["name"])})
        org_id = factories.Organization()["id"]

        for _ in range(3):
            dataset = dataset_factory(default_data_schema="",
                                      owner_org=org_id,
                                      de_identified_data="YES")
            resource_factory(package_id=dataset["id"])
            call_action("package_patch",
                        context=_make_context(),
                        id=dataset["id"],
                        notes="test")

        result = helpers.gather_admin_metrics(org_id, "admin")

        assert result["datasets_no_groups"] == 3
        assert result["datasets_no_tags"] == 3
        assert result["de_identified_datasets"] == 3
        assert result["de_identified_datasets_no_schema"] == 3
        assert result["overdue_datasets"] == 0
        assert result["pending_privacy_assessment"] == 0

    @pytest.mark.ckan_config(
        u"ckanext.data_qld.reporting.de_identified_no_schema.count_from",
        u"2045-01-01")
    def test_set_de_identified_count_from_in_future(self, app, dataset_factory,
                                                    resource_factory,
                                                    sysadmin):
        app.get('/', extra_environ={"REMOTE_USER": str(sysadmin["name"])})
        org_id = factories.Organization()["id"]

        for _ in range(3):
            dataset = dataset_factory(default_data_schema="",
                                      owner_org=org_id,
                                      de_identified_data="YES")
            resource_factory(package_id=dataset["id"])

        result = helpers.gather_admin_metrics(org_id, "admin")

        assert result["de_identified_datasets_no_schema"] == 0

    @pytest.mark.ckan_config(
        u"ckanext.data_qld.reporting.de_identified_no_schema.count_from",
        u"2022-12-01T01:00")
    @pytest.mark.parametrize(
        "count_from, pkg_counter",
        [
            ("2022-12-01T02:00", 1),
            ("2022-12-01T01:00:49.982971", 1),
            ("2022-12-01T00:59", 0),
        ],
    )
    def test_de_identified_parametrize(self, app, dataset_factory, sysadmin,
                                       count_from, pkg_counter):
        app.get('/', extra_environ={"REMOTE_USER": str(sysadmin["name"])})
        org_id = factories.Organization()["id"]

        dataset = dataset_factory(
            default_data_schema="",
            de_identified_data="YES",
            owner_org=org_id,
        )

        package = model.Session.query(model.Package).get(dataset["id"])
        package._extras["data_last_updated"] = model.PackageExtra(
            value=count_from, key="data_last_updated")
        model.Session.commit()

        result = helpers.gather_admin_metrics(org_id, "admin")

        assert result[u"de_identified_datasets_no_schema"] == pkg_counter


@pytest.mark.usefixtures("with_plugins", "with_request_context", "clean_db",
                         "mock_storage", "do_not_validate")
class TestAdminReportPendingPrivacyAssessment:

    def test_with_pending_resource(self, dataset_factory, resource_factory):
        dataset = dataset_factory()
        resource_factory(package_id=dataset["id"],
                         request_privacy_assessment="YES")

        counter = call_action("datasets_pending_privacy_assessment",
                              _make_context(),
                              org_id=dataset["owner_org"],
                              return_count_only=True)

        assert counter == 1

    def test_without_pending_resource(self):
        counter = call_action("datasets_pending_privacy_assessment",
                              _make_context(),
                              org_id=factories.Organization()["id"],
                              return_count_only=True)

        assert counter == 0

    def test_with_multiple_packages(self, dataset_factory, resource_factory):
        dataset = dataset_factory()

        for _ in range(3):
            resource_factory(package_id=dataset["id"],
                             request_privacy_assessment="YES")

        counter = call_action("datasets_pending_privacy_assessment",
                              _make_context(),
                              org_id=dataset["owner_org"],
                              return_count_only=True)

        assert counter == 3

    def test_without_org_id(self, dataset_factory, resource_factory):
        dataset = dataset_factory(default_data_schema="")
        resource_factory(package_id=dataset["id"])

        counter = call_action("datasets_pending_privacy_assessment",
                              _make_context(),
                              return_count_only=True)

        assert counter == 0


def _make_context():
    sysadmin = factories.Sysadmin()
    return {"user": sysadmin["name"], "ignore_auth": True}
