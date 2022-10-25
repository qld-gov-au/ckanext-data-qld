# encoding: utf-8

import ckantoolkit as tk
from six import string_types
from six.moves.urllib.parse import urlparse


def is_api_call():
    controller, action = tk.get_endpoint()

    resource_edit = (controller == "resource" and action == "edit") or \
                    (controller == "package" and action == "resource_edit")
    resource_create = action == "new_resource"

    return False if (resource_edit or resource_create) else True


def is_url_valid(url):
    """Basic checks for url validity"""
    if not isinstance(url, string_types):
        return False

    try:
        tokens = urlparse(url)
    except ValueError:
        return False

    return all([getattr(tokens, attr) for attr in ('scheme', 'netloc')])
