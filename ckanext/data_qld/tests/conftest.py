# encoding: utf-8

import os
import json
import six
from datetime import datetime as dt

import pytest
import factory
from faker import Faker
from werkzeug.datastructures import FileStorage as MockFileStorage

import ckan.tests.helpers as helpers
from ckan.tests import factories

from ckan.lib import uploader
from ckanext.qa.cli.commands import init_db as qa_init
from ckanext.ytp.comments.model import init_tables as ytp_init
from ckanext.validation.model import create_tables as validation_init
from ckanext.validation.model import tables_exist as is_validation_table_exist
from ckanext.archiver import utils as archiver_utils

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
    default_data_schema = factory.LazyAttribute(lambda _: _get_default_schema())
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

    package_id = factory.LazyAttribute(lambda _: DatasetFactory()["id"])

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        kwargs.setdefault("context", {})
        return helpers.call_action("resource_create", **kwargs)


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
        "missingValues": ["Resource schema"]
    }

    return json.dumps(schema)


def _get_default_schema():
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
        "missingValues": ["Default schema"]
    }
    return json.dumps(schema)


class SysadminFactory(factories.Sysadmin):
    password = "Password123!"


@pytest.fixture
def sysadmin():
    return SysadminFactory()


@pytest.fixture
def sysadmin_factory():
    return SysadminFactory


class UserFactory(factories.User):
    password = "Password123!"


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def user_factory():
    return UserFactory


@pytest.fixture
def clean_db(reset_db):
    reset_db()

    archival_init()
    qa_init()
    ytp_init()

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
