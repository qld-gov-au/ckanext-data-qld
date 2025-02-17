# encoding: utf-8

import json
from datetime import datetime as dt

import pytest
import factory
from faker import Faker

from ckan import model
from ckan.tests import factories, helpers

from ckan.lib import uploader
from ckan.plugins.toolkit import check_ckan_version

from ckanext.datarequests import db as datarequest_db
from ckanext.qa.cli.commands import init_db as qa_init
from ckanext.ytp.comments import model as ytp_model
from ckanext.validation.model import create_tables as validation_init
from ckanext.archiver import utils as archiver_utils

fake = Faker()


class OrganizationFactory(factories.Organization):
    name = factory.LazyAttribute(
        lambda _: fake.slug() + "" + dt.now().strftime("%Y%m%d-%H%M%S"))


class DatasetFactory(factories.Dataset):
    name = factory.LazyAttribute(
        lambda _: fake.slug() + "" + dt.now().strftime("%Y%m%d-%H%M%S"))
    update_frequency = "non-regular"
    author_email = factory.LazyAttribute(lambda _: fake.email())
    version = "1.0"
    license_id = "other-open"
    data_driven_application = "NO"
    security_classification = "PUBLIC"
    de_identified_data = "NO"
    owner_org = factory.LazyAttribute(lambda _: factories.Organization()["id"])


@pytest.fixture
def dataset_factory():
    return DatasetFactory


@pytest.fixture
def dataset():
    return DatasetFactory()


class ResourceFactory(factories.Resource):
    """ Provide some necessary defaults to ensure that eg we use a valid format
    """
    privacy_assessment_result = "Foo"
    resource_visible = "TRUE"
    schema = ""
    format = "CSV"


@pytest.fixture
def resource_factory():
    return ResourceFactory


@pytest.fixture
def resource_schema():
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


@pytest.fixture
def dataset_schema():
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


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()
    if check_ckan_version('2.11'):
        migrate_db_for('activity')

    archival_init()
    qa_init()
    ytp_model.init_tables()
    datarequest_db.init_db(model)

    validation_init()


def archival_init():
    archiver_utils.initdb()
    archiver_utils.migrate()


@pytest.fixture
def mock_storage(monkeypatch, ckan_config, tmpdir):
    monkeypatch.setitem(ckan_config, u'ckan.storage_path', str(tmpdir))
    monkeypatch.setattr(uploader, u'get_storage_path', lambda: str(tmpdir))


@pytest.fixture
def do_not_validate(monkeypatch):
    """Skip resource validation"""

    monkeypatch.setattr(
        "ckanext.validation.utils.is_resource_could_be_validated",
        lambda a, b: False)


class Comment(factory.Factory):
    """A factory class for creating ytp comment. It must accept user_id and
    package_name, because I don't want to create extra entities in database
    during tests"""

    class Meta:
        model = ytp_model.Comment

    user_id = None
    entity_type = "dataset"
    entity_name = None

    subject = "comment-subject"
    comment = "comment-text"

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        kwargs["url"] = "/{}/{}".format(kwargs["entity_type"], kwargs["entity_name"])

        return helpers.call_action(
            "comment_create", context={"user": kwargs["user_id"], "ignore_auth": True}, **kwargs
        )


@pytest.fixture
def comment_factory():
    return Comment


class DataRequest(factory.Factory):
    """Datarequest factory"""

    class Meta:
        model = datarequest_db.DataRequest

    id = factory.LazyAttribute(lambda _: fake.uuid4())
    user_id = factory.LazyAttribute(lambda _: factories.User()["id"])
    title = factory.LazyAttribute(lambda _: fake.sentence())
    description = factory.LazyAttribute(lambda _: fake.sentence())
    open_time = factory.LazyAttribute(lambda _: str(dt.utcnow()))
    organization_id = factory.LazyAttribute(lambda _: factories.Organization()["id"])

    @classmethod
    def _build(cls, target_class, *args, **kwargs):
        raise NotImplementedError(".build() isn't supported in CKAN")

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        if args:
            assert False, "Positional args aren't supported, use keyword args."

        user_obj = model.Session.query(model.User).get(kwargs["user_id"])

        return helpers.call_action(
            "create_datarequest", context={"auth_user_obj": user_obj}, **kwargs
        )


@pytest.fixture
def datarequest_factory():
    return DataRequest
