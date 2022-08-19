# encoding: utf-8

import ckantoolkit as tk

from ckan import plugins

from ckanext.data_qld.tests.conftest import DatasetFactory


class DataQldTestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)

    # IActions

    def get_actions(self):
        return {
            'qld_test_create_dataset': qld_test_create_dataset,
            'qld_test_purge_dataset': qld_test_purge_dataset
        }


@tk.side_effect_free
def qld_test_create_dataset(context, data_dict):
    tk.check_access("site_read", context)
    return DatasetFactory(**data_dict)

@tk.side_effect_free
def qld_test_purge_dataset(context, data_dict):
    context = {"ignore_auth": True}
    user_obj = tk.get_action("get_site_user")(context, {})

    pkg_dict = tk.get_action("package_show")({"user": user_obj['name']}, data_dict)

    tk.get_action("dataset_purge")({"user": user_obj['name']}, data_dict)
    tk.get_action("organization_purge")(
        {"user": user_obj['name']},
        {"id": pkg_dict["owner_org"]}
    )
