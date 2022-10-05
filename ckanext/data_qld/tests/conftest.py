import os
import json
import six
import tempfile
from datetime import datetime as dt

import pytest
import factory
from factory import Faker
from mock import patch

import ckan.tests.helpers as helpers
from ckan.tests import factories
from ckan.tests.pytest_ckan.fixtures import FakeFileStorage
from ckan.lib import uploader
from ckan.common import config

from ckanext.qa.cli.commands import init_db as qa_init
from ckanext.harvest.model import setup as harvest_init
from ckanext.ytp.comments.model import init_tables as ytp_init
from ckanext.validation.model import create_tables as validation_init
from ckanext.validation.model import tables_exist as is_validation_table_exist
from ckanext.archiver import utils as archiver_utils


class OrganizationFactory(factories.Organization):
    name = factory.LazyFunction(lambda: Faker("slug").generate() + "" + dt.now(
    ).strftime("%Y%m%d-%H%M%S"))


class DatasetFactory(factories.Dataset):
    name = factory.LazyFunction(lambda: Faker("slug").generate() + "" + dt.now(
    ).strftime("%Y%m%d-%H%M%S"))
    update_frequency = "monthly"
    author_email = Faker("email")
    version = "1.0"
    license_id = "other-open"
    data_driven_application = "NO"
    security_classification = "PUBLIC"
    de_identified_data = "NO"
    owner_org = factory.LazyFunction(lambda: OrganizationFactory()["id"])
    validation_options = ""
    validation_status = ""
    validation_timestamp = ""
    default_data_schema = '{"fields": [{"name": "x", "title": "Default schema", "type": "integer"}],"primaryKey":"x"}'
    schema_upload = ""
    schema_json = ""


@pytest.fixture
def dataset_factory():
    return DatasetFactory


@pytest.fixture
def dataset():
    return DatasetFactory()


class ResourceFactory(factories.Resource):
    id = factory.Faker("uuid4")
    description = factory.Faker("sentence")
    name = factory.LazyFunction(lambda: factory.Faker("slug").generate() + "" +
                                dt.now().strftime("%Y%m%d-%H%M%S"))
    privacy_assessment_result = factory.LazyFunction(
        lambda: factory.Faker("sentence").generate())
    last_modified = factory.LazyFunction(lambda: str(dt.now()))
    resource_visible = "TRUE"
    schema = factory.LazyFunction(lambda: _get_resource_schema())

    upload = factory.LazyFunction(lambda: _get_test_file())
    format = "csv"
    url_type = "upload"
    url = None

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        if kwargs.get('bdd'):
            return helpers.call_action("resource_create", context={}, **kwargs)

        temp_dir = str(tempfile.mkdtemp())
        with patch.object(uploader, u'_storage_path', temp_dir):
            with patch.dict(config, {u'ckan.storage_path': temp_dir}):
                resource_dict = helpers.call_action("resource_create",
                                                    context={},
                                                    **kwargs)
        return resource_dict


def _get_test_file():
    file_path = os.path.join(os.path.dirname(__file__), 'data/test.csv')

    with open(file_path) as file:
        test_file = six.BytesIO()
        test_file.write(six.ensure_binary(file.read()))
        test_file.seek(0)

        return FakeFileStorage(test_file, "test.csv")


def _get_resource_schema():
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

    return json.dumps(schema)


class SysadminFactory(factories.Sysadmin):
    pass


@pytest.fixture
def sysadmin():
    return SysadminFactory()


class UserFactory(factories.User):
    pass


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def clean_db(reset_db):
    reset_db()

    archival_init()
    qa_init()
    harvest_init()
    ytp_init()

    if not is_validation_table_exist():
        validation_init()


def archival_init():
    archiver_utils.initdb()
    archiver_utils.migrate()
