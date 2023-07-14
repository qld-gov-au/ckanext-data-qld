import logging

import ckan.plugins.toolkit as tk
import ckan.lib.search as search

from ckanext.ytp.comments import signals, model as ytp_model

log = logging.getLogger(__name__)


@signals.deleted.connect
def after_comment_delete(thread_id, comment):
    _trigger_package_index_on_comment(thread_id)


@signals.created.connect
def after_comment_created(thread_id, comment):
    _trigger_package_index_on_comment(thread_id)


@signals.updated.connect
def after_comment_updated(thread_id, comment):
    _trigger_package_index_on_comment(thread_id)


def _trigger_package_index_on_comment(thread_id):
    """We want to search by comment title/content, so we have to trigger
    a package index each time, when we are creating/updating/deleting the comment.
    Then, in the before_index we are going to index mentioned info along with the
    package metadata"""
    thread = ytp_model.CommentThread.get(thread_id)

    content_type, entity_id = _parse_thread_content(thread)

    if content_type == "datarequest":
        return

    package = _get_package_object(entity_id)

    if not package:
        return

    index = search.PackageSearchIndex()
    index.update_dict(package)


def _parse_thread_content(thread):
    """
    Parse a thread url field to content_type and id

    e.g. /datarequest/0c9bfd23-49d0-47ce-ad2b-6195519dfa5e
         /dataset/df8e9120-ebeb-4945-abda-eb3df8c7b61b
         /dataset/test-ds-1
    """
    return thread.url.strip("/").split("/")


def _get_package_object(package_id):
    try:
        return tk.get_action("package_show")({"ignore_auth": True}, {"id": package_id})
    except tk.ObjectNotFound:
        return
