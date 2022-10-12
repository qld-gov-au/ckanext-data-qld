import os
import json
import six
from datetime import datetime as dt

import pytest
import factory
import ckantoolkit as tk
from faker import Faker

import ckan.tests.helpers as helpers
from ckan.tests import factories

from ckan.lib import uploader
from ckanext.validation.model import create_tables as validation_init
from ckanext.validation.model import tables_exist as is_validation_table_exist
from ckanext.archiver import utils as archiver_utils

if tk.check_ckan_version('2.9'):
    from werkzeug.datastructures import FileStorage as MockFileStorage
else:
    import cgi

    class MockFileStorage(cgi.FieldStorage):

        def __init__(self, fp, filename):

            self.file = fp
            self.filename = filename
            self.name = u"upload"
            self.list = None


fake = Faker()


class OrganizationFactory(factories.Organization):
    name = factory.LazyAttribute(
        lambda _: fake.slug() + "" + dt.now().strftime("%Y%m%d-%H%M%S"))


class DatasetFactory(factories.Dataset):
    name = factory.LazyAttribute(
        lambda _: fake.slug() + "" + dt.now().strftime("%Y%m%d-%H%M%S"))
    update_frequency = "monthly"
    author_email = factory.LazyAttribute(lambda _: fake.email())
    version = "1.0"
    license_id = "other-open"
    data_driven_application = "NO"
    security_classification = "PUBLIC"
    de_identified_data = "NO"
    owner_org = factory.LazyAttribute(lambda _: OrganizationFactory()["id"])
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
    id = factory.LazyAttribute(lambda _: fake.uuid4())
    description = factory.LazyAttribute(lambda _: fake.sentence())
    name = factory.LazyAttribute(
        lambda _: fake.slug() + "" + dt.now().strftime("%Y%m%d-%H%M%S"))
    privacy_assessment_result = factory.LazyAttribute(
        lambda _: fake.sentence())
    last_modified = factory.LazyAttribute(lambda _: str(dt.now()))
    resource_visible = "TRUE"
    schema = factory.LazyAttribute(lambda _: _get_resource_schema())

    upload = factory.LazyAttribute(lambda _: _get_test_file())
    format = "csv"
    url_type = "upload"
    url = None

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        return helpers.call_action("resource_create", context={}, **kwargs)


@pytest.fixture
def resource_factory():
    return ResourceFactory


@pytest.fixture
def resource():
    return ResourceFactory()


def _get_test_file():
    file_path = os.path.join(os.path.dirname(__file__), 'data/test.csv')

    with open(file_path) as file:
        test_file = six.BytesIO()
        test_file.write(six.ensure_binary(file.read()))
        test_file.seek(0)

        return MockFileStorage(test_file, "test.csv")


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

    if not is_validation_table_exist():
        validation_init()


def archival_init():
    archiver_utils.initdb()
    archiver_utils.migrate()


@pytest.fixture
def mock_storage(monkeypatch, ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, u'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(uploader, u'_storage_path', str(tmpdir))


@pytest.fixture
def do_not_validate(monkeypatch):
    """Skip resource validation"""

    monkeypatch.setattr(
        "ckanext.validation.utils.is_resource_could_be_validated",
        lambda a, b: False)
