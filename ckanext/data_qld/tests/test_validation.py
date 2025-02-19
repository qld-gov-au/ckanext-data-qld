import pytest
import mock

from ckan.tests import factories

import ckanext.validation.settings as validation_settings


@pytest.mark.usefixtures("with_plugins", "with_request_context", "mock_storage")
@pytest.mark.ckan_config(validation_settings.ASYNC_CREATE_KEY, True)
class TestValidationDefineCreateMode:

    def test_get_create_mode_if_has_schema_and_de_identified(
            self, dataset_factory, resource_factory, resource_schema):
        """Validation must be in sync mode if we have a schema and dataset
        is de_identified"""
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"], schema=resource_schema)

        mode = validation_settings.get_create_mode({}, resource)
        assert mode == validation_settings.SYNC_MODE

    def test_get_create_mode_if_no_schema_and_de_identified(
            self, dataset_factory, resource_factory):
        """Validation must be in async mode if we don't have a schema and dataset
        is de_identified"""
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"], schema=None)

        mode = validation_settings.get_create_mode({}, resource)
        assert mode == validation_settings.ASYNC_MODE

    def test_get_create_mode_if_has_schema_and_not_de_identified(
            self, dataset_factory, resource_factory, resource_schema):
        """Validation must be in async mode if we have a schema and dataset
        is de_identified"""
        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"], schema=resource_schema)

        mode = validation_settings.get_create_mode({}, resource)
        assert mode == validation_settings.ASYNC_MODE

    @mock.patch("ckanext.data_qld.utils.is_api_call", lambda: False)
    def test_get_create_mode_if_no_schema_and_de_identified_but_aligned(
            self, dataset_factory, resource_factory):
        """Validation must be in sync mode if we don't have a schema and dataset
        is de_identified, but resource schema is aligned with default schema"""
        sysadmin = factories.Sysadmin()
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"],
                                    schema=None,
                                    align_default_schema=1,
                                    context={"ignore_auth": False, "user": sysadmin["name"]})

        mode = validation_settings.get_create_mode({}, resource)
        assert mode == validation_settings.SYNC_MODE


@pytest.mark.usefixtures("with_plugins", "with_request_context", "mock_storage")
@pytest.mark.ckan_config(validation_settings.ASYNC_UPDATE_KEY, True)
class TestValidationDefineUpdateMode:

    def test_get_update_mode_if_has_schema_and_de_identified(
            self, dataset_factory, resource_factory, resource_schema):
        """Validation must be in sync mode if we have a schema and dataset
        is de_identified"""
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"], schema=resource_schema)

        mode = validation_settings.get_update_mode({}, resource)
        assert mode == validation_settings.SYNC_MODE

    def test_get_update_mode_if_no_schema_and_de_identified(
            self, dataset_factory, resource_factory):
        """Validation must be in async mode if we don't have a schema and dataset
        is de_identified"""
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"], schema=None)

        mode = validation_settings.get_update_mode({}, resource)
        assert mode == validation_settings.ASYNC_MODE

    def test_get_update_mode_if_has_schema_and_not_de_identified(
            self, dataset_factory, resource_factory, resource_schema):
        """Validation must be in async mode if we have a schema and dataset
        is de_identified"""
        dataset = dataset_factory()
        resource = resource_factory(package_id=dataset["id"], schema=resource_schema)

        mode = validation_settings.get_update_mode({}, resource)
        assert mode == validation_settings.ASYNC_MODE

    @mock.patch("ckanext.data_qld.utils.is_api_call", lambda: False)
    def test_get_update_mode_if_no_schema_and_de_identified_but_aligned(
            self, dataset_factory, resource_factory):
        """Validation must be in sync mode if we don't have a schema and dataset
        is de_identified, but resource schema is aligned with default schema"""
        sysadmin = factories.Sysadmin()
        dataset = dataset_factory(de_identified_data="YES")
        resource = resource_factory(package_id=dataset["id"],
                                    schema=None,
                                    align_default_schema=1,
                                    context={"ignore_auth": False, "user": sysadmin["name"]})

        mode = validation_settings.get_update_mode({}, resource)
        assert mode == validation_settings.SYNC_MODE
