# encoding: utf-8

import re
import ckantoolkit as tk
from six import string_types
from six.moves.urllib.parse import urlparse
from bs4 import BeautifulSoup


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


def get_comments_data_for_index(thread):
    chunks = []

    for comment in thread["comments"]:
        if comment["state"] != "active":
            continue

        chunks.append(strip_html_tags(comment["content"]))
        chunks.append(comment["subject"])

    return _munge_to_string(set(chunks))


def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")

    return re.sub("\r", " ", soup.get_text()).strip()


def _munge_to_string(chunks):
    unique_words = set()

    for chunk in chunks:
        words = chunk.split()
        unique_words.update(words)

    return " ".join(unique_words)
