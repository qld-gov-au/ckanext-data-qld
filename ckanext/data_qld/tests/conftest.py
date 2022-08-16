from random import randint

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
    pass

register(OrganizationFactory, "organization")

class DatasetFactory(factories.Dataset):
    update_frequency = "monthly"
    author_email = factory.Faker("email")
    version = "1.0"
    license_id = "other-open"
    data_driven_application = "NO"
    security_classification = "PUBLIC"
    de_identified_data = "NO"
    owner_org=factory.LazyFunction(lambda: OrganizationFactory()["id"])
    schema = ""
    schema_upload = ""
    validation_options = ""
    validation_status = ""
    validation_timestamp = ""

register(DatasetFactory, "dataset")


class ResourceFactory(factories.Resource):
    size = randint(1, 1000)
    format = "csv"

register(ResourceFactory, "resource")


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
