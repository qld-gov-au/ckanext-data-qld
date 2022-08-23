# encoding: utf-8

import ckantoolkit as tk

from ckan import plugins

from ckanext.data_qld.tests.conftest import DatasetFactory, ResourceFactory


class DataQldTestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)

    # IActions

    def get_actions(self):
        return {
            'qld_test_create_dataset': qld_test_create_dataset,
            'qld_test_purge_dataset': qld_test_purge_dataset,
            'qld_test_patch_dataset': qld_test_patch_dataset
        }


@tk.side_effect_free
def qld_test_create_dataset(context, data_dict):
    package = DatasetFactory(**data_dict)
    ResourceFactory(package_id=package["id"])

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


def _make_context():
    context = {"ignore_auth": True}
    user_obj = tk.get_action("get_site_user")(context, {})
    return {"user": user_obj['name']}
