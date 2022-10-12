from io import StringIO

import pytest

from werkzeug.datastructures import FileStorage

from ckan.tests import factories
import ckan.logic as logic


@pytest.mark.usefixtures("with_plugins", "clean_db", "mock_storage")
class TestCreateData:

    def test_create_dataset_and_resource(self, dataset_factory,
                                         resource_factory):
        organization = factories.Organization()
        dataset = dataset_factory(owner_org=organization["id"])
        resource = resource_factory(package_id=dataset["id"])

        assert resource

    def test_restricted_resource_format(self, dataset, resource_factory):
        resource = resource_factory(package_id=dataset["id"], format="CSV")

        assert resource["format"] == "CSV"

        with pytest.raises(logic.ValidationError):
            resource_factory(package_id=dataset["id"], format="_FORMAT")

    def test_resource_request_privacy_assessment(self, dataset,
                                                 resource_factory):
        resource_factory(package_id=dataset["id"], format="CSV")

        resource_factory(package_id=dataset["id"],
                         format="CSV",
                         request_privacy_assessment="NO")
        resource_factory(package_id=dataset["id"],
                         format="CSV",
                         request_privacy_assessment="YES")

        with pytest.raises(logic.ValidationError):
            resource_factory(package_id=dataset["id"],
                             format="_FORMAT",
                             request_privacy_assessment="OF COURSE")

    def test_upload_schema(self, dataset_factory):
        stream = StringIO(
            u'{"fields": [{"name": "x", "title": "X", "type": "integer"}],"primaryKey":"x"}'
        )
        schema_file = FileStorage(stream,
                                  "schema.json",
                                  content_type="application/json")
        dataset = dataset_factory(schema_upload=schema_file)

        assert dataset["default_data_schema"]
        assert not dataset['schema_upload']

    def test_json_schema(self, dataset_factory):
        dataset = dataset_factory()

        assert dataset["default_data_schema"]
        assert not dataset['schema_upload']
