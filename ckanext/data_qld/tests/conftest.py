from random import randint
from datetime import datetime as dt

import pytest
import factory
from ckan.tests import factories
from pytest_factoryboy import register

from ckanext.qa.cli.commands import init_db as qa_init
from ckanext.harvest.model import setup as harvest_init
from ckanext.ytp.comments.model import init_tables as ytp_init
from ckanext.validation.model import create_tables as validation_init
from ckanext.validation.model import tables_exist as is_validation_table_exist


class OrganizationFactory(factories.Organization):
    name = factory.LazyFunction(lambda: factory.Faker("slug").generate() + "" +
                                dt.now().strftime("%Y%m%d-%H%M%S"))
    pass


register(OrganizationFactory, "organization")


class DatasetFactory(factories.Dataset):
    name = factory.LazyFunction(lambda: factory.Faker("slug").generate() + "" +
                                dt.now().strftime("%Y%m%d-%H%M%S"))
    update_frequency = "monthly"
    author_email = factory.Faker("email")
    version = "1.0"
    license_id = "other-open"
    data_driven_application = "NO"
    security_classification = "PUBLIC"
    de_identified_data = "YES"
    owner_org = factory.LazyFunction(lambda: OrganizationFactory()["id"])
    validation_options = ""
    validation_status = ""
    validation_timestamp = ""
    default_data_schema = '{"fields": [{"name": "x", "title": "X", "type": "integer"}],"primaryKey":"x"}'
    schema_upload = ""
    schema_json = ""
    resources = [{
        "url": factory.Faker("url").generate(),
        "format": "CSV",
        "name": factory.Faker("slug").generate(),
        "description": factory.Faker("sentence").generate(),
        "size": randint(1, 1000),
        "last_modified": str(dt.now()),
        "privacy_assessment_result": factory.Faker("sentence").generate()
    }]


register(DatasetFactory, "dataset")


class ResourceFactory(factories.Resource):
    id = factory.Faker("uuid4")
    url = factory.Faker("url")
    description = factory.Faker("sentence")
    size = randint(1, 1000)
    format = "CSV"
    name = factory.LazyFunction(lambda: factory.Faker("slug").generate() + "" +
                                dt.now().strftime("%Y%m%d-%H%M%S"))
    privacy_assessment_result = factory.LazyFunction(
        lambda: factory.Faker("sentence").generate())
    last_modified = factory.LazyFunction(lambda: str(dt.now()))
    resource_visible = "TRUE"


register(ResourceFactory, "resource")


class SysadminFactory(factories.Sysadmin):
    pass


register(SysadminFactory, "sysadmin")


class UserFactory(factories.User):
    pass


register(UserFactory, "user")


@pytest.fixture()
def clean_db(reset_db):
    reset_db()

    archival_init()
    qa_init()
    harvest_init()
    ytp_init()

    if not is_validation_table_exist():
        validation_init()


def archival_init():
    from ckanext.archiver.cli import ArchivalCommands

    ArchivalCommands().initdb()
    ArchivalCommands().migrate()
