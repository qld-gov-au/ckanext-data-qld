# encoding: utf-8

import logging

from ckan import model
import ckantoolkit as tk

from ckanext.datarequests import actions as datarequest_actions, db
from ckanext.ytp.comments.model import Comment, CommentThread

from . import constants

log = logging.getLogger(__name__)

ORIG_DICTIZE_DATAREQUEST = datarequest_actions._dictize_datarequest


def intercept():
    datarequest_actions._dictize_datarequest = _dictize_datarequest


def _dictize_datarequest(datarequest):
    data_dict = ORIG_DICTIZE_DATAREQUEST(datarequest)
    data_dict['datarequest_url'] = tk.url_for('datarequest.show', id=datarequest.id, qualified=True)
    return data_dict


def open_datarequest(context, data_dict):
    """
    Action to open a data request. Access rights will be checked before
    opening the data request. If the user is not allowed, a NotAuthorized
    exception will be risen.

    :param id: The ID of the data request to be closed
    :type id: string

    :returns: A dict with the data request (id, user_id, title, description,
        organization_id, open_time, accepted_dataset, close_time, closed,
        followers)
    :rtype: dict

    """

    model = context['model']
    session = context['session']
    datarequest_id = data_dict.get('id', '')

    # Check id
    if not datarequest_id:
        raise tk.ValidationError(tk._('Data Request ID has not been included'))

    # Init the data base if needed
    if not db.DataRequest:
        db.init_db(model)

    # Check access
    tk.check_access(constants.OPEN_DATAREQUEST, context, data_dict)

    # Get the data request
    result = db.DataRequest.get(id=datarequest_id)

    if not result:
        raise tk.ObjectNotFound(
            tk._('Data Request %s not found in the data base') % datarequest_id)

    data_req = result[0]
    data_req.closed = False
    data_req.accepted_dataset_id = None
    data_req.close_time = None
    if tk.h.closing_circumstances_enabled:
        data_req.close_circumstance = None
        data_req.approx_publishing_date = None

    session.add(data_req)
    session.commit()

    datarequest_dict = _dictize_datarequest(data_req)

    # Mailing
    users = [data_req.user_id]
    # Creator email
    datarequest_actions._send_mail(
        users, 'open_datarequest_creator', datarequest_dict,
        'Data Request Opened Creator Email'
    )
    if datarequest_dict['organization']:
        users = datarequest_actions._get_admin_users_from_organisation(datarequest_dict)
        # Admins of organisation email
        datarequest_actions._send_mail(
            users, 'open_datarequest_organisation', datarequest_dict,
            'Data Request Opened Admins Email'
        )

    return datarequest_dict


@tk.chained_action
def list_datarequests(original_action, context, data_dict):
    """By default the ckanext-datarequest `list_datarequests` action searches
    only inside datarequest title and description. We are altering it, to search
    by a comments, related to the datarequest entity.

    The comments are implemented via ckanext-ytp-comments
    """
    result = original_action(context, data_dict)

    if not tk.h.ytp_comments_enabled():
        return result

    query = data_dict.get("q", "")
    if not query:
        return result
    sort = data_dict.get("sort", "desc")

    datarequest_ids = _search_by_datarequest_comments(query)
    existing_ids = [dr["id"] for dr in result["result"]]

    for datarequest_id in datarequest_ids:
        if datarequest_id in existing_ids:
            continue

        try:
            data = tk.get_action("show_datarequest")({}, {"id": datarequest_id})
        except tk.ObjectNotFound:
            continue

        result["result"].append(data)

    _sort_datarequests(result["result"], sort)
    result["count"] = len(result["result"])

    return result


def _search_by_datarequest_comments(query):
    search_pattern = '%{}%'.format(query)
    threads = model.Session.query(CommentThread.url) \
        .filter(CommentThread.url.like("/datarequest/%")) \
        .join(Comment) \
        .filter((Comment.subject.ilike(search_pattern))
                | (Comment.comment.ilike(search_pattern))) \
        .all()

    return [thread.url.strip("/").split("/")[1] for thread in threads]


def _sort_datarequests(datarequests, sort):
    datarequests.sort(key=lambda x: x["open_time"], reverse=sort == "desc")
