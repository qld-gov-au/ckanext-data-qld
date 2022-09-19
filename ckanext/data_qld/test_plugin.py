# encoding: utf-8
import os

import ckantoolkit as tk
from werkzeug.datastructures import FileStorage

from ckan import plugins

from ckanext.data_qld.tests.conftest import DatasetFactory, ResourceFactory
import ckanext.resource_visibility.utils as utils


class DataQldTestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)

    # IActions

    def get_actions(self):
        return {
            'qld_test_create_dataset': qld_test_create_dataset,
            'qld_test_purge_dataset': qld_test_purge_dataset,
            'qld_test_patch_dataset': qld_test_patch_dataset,
            'qld_test_create_resource_for_dataset': qld_test_create_resource_for_dataset,
            'qld_test_trigger_notify_privacy_assessment_result': qld_test_trigger_notify_privacy_assessment_result
        }


@tk.side_effect_free
def qld_test_create_dataset(context, data_dict):
    package = DatasetFactory(**data_dict)

    here = os.path.dirname(__file__)
    with open(os.path.join(here, 'sample.csv')) as f:
        file = FileStorage(f, "sample.csv", content_type="text/csv")
        ResourceFactory(package_id=package["id"], upload=file)

    return package


@tk.side_effect_free
def qld_test_purge_dataset(context, data_dict):
    context = _make_context()
    pkg_dict = tk.get_action("package_show")(context, data_dict)

    tk.get_action("dataset_purge")(context, data_dict)
    tk.get_action("organization_purge")(context,{"id": pkg_dict["owner_org"]})


@tk.side_effect_free
def qld_test_patch_dataset(context, data_dict):
    tk.get_action("package_patch")(_make_context(), data_dict)


@tk.side_effect_free
def qld_test_create_resource_for_dataset(context, data_dict):
    resource = ResourceFactory(**data_dict)

    return resource


@tk.side_effect_free
def qld_test_trigger_notify_privacy_assessment_result(context, data_dict):
    data = utils.get_updated_privacy_assessment_result()

    if not data:
        return

    for maintainer_email, updated_data in data.items():
        utils.send_notifications(maintainer_email, updated_data.values())
        utils._clear_upd_assessment_result_data()



def _make_context():
    context = {"ignore_auth": True}
    user_obj = tk.get_action("get_site_user")(context, {})
    return {"user": user_obj['name']}
