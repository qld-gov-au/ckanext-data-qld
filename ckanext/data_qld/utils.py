# encoding: utf-8

import ckantoolkit as tk


def is_api_call():
    controller, action = tk.get_endpoint()

    resource_edit = ((controller == "resource" and action == "edit") or
                     (controller == "package" and action == "resource_edit"))
    resource_create = action == "new_resource"

    return False if (resource_edit or resource_create) else True
