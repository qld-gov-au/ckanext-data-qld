# encoding: utf-8

import logging
from datetime import datetime, timedelta

import sqlalchemy
import pytz
from sqlalchemy import func, distinct, tuple_, and_
from sqlalchemy.orm import aliased
from ckantoolkit import config, NotAuthorized, h

from ckan import model
from ckan.model.follower import UserFollowingDataset, UserFollowingGroup

from ckanext.ytp.comments.model import Comment, CommentThread
from ckanext.ytp.comments.notification_models import CommentNotificationRecipient
from ckanext.datarequests import db

from ckanext.data_qld.reporting import constants
from ckanext.data_qld.reporting.helpers import helpers

from ckanext.resource_visibility.constants import FIELD_REQUEST_ASSESS, YES


_and_ = sqlalchemy.and_
_replace_ = func.replace
_session_ = model.Session
check_org_access = helpers.check_user_org_access
check_user_access = helpers.check_user_access
log = logging.getLogger(__name__)

#
ACTIVE_STATE = 'active'
DATAREQUEST_PREFIX = '/datarequest/'
DATAREQUEST_LIKE = DATAREQUEST_PREFIX + '%'
DATASET_PREFIX = '/dataset/'
DATASET_LIKE = DATASET_PREFIX + '%'


def _authorised_orgs(data_dict, context):
    """
    Retrieve the organisation ID(s), check that the current user
    has the specified level of privileges in the org (default 'admin'),
    and return the organisation ID(s) as a list.
    """
    org_id = data_dict.get('org_id', None)
    permission = data_dict.get('permission', 'admin')
    check_org_access(org_id, permission, context=context)
    # handle single-org syntax just in case
    if isinstance(org_id, list):
        return org_id, True
    else:
        return [org_id], False


def _active_package_query(org_id, is_org_list, return_count_only):
    """
    Assembles a partial query object, setting common filters.
    """
    if return_count_only and is_org_list:
        query = _session_.query(model.Package.owner_org, func.count(model.Package.id)) \
            .group_by(model.Package.owner_org)
    else:
        query = _session_.query(model.Package)
    return query.filter(model.Package.owner_org.in_(org_id)) \
        .filter(model.Package.state == ACTIVE_STATE)


def _query_result(query, is_org_list, return_count_only):
    return query.count() if return_count_only and not is_org_list else query.all()


def organisation_followers(context, data_dict):
    """
    Return the number of followers for an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        return (
            _session_.query(
                func.count(UserFollowingGroup.follower_id)
            )
            .filter(
                _and_(
                    model.Group.id == org_id,
                    UserFollowingGroup.datetime >= utc_start_date,
                    UserFollowingGroup.datetime < utc_end_date,
                )
            )
            .join(model.Group, model.Group.id == UserFollowingGroup.object_id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_followers(context, data_dict):
    """
    Return the number of followers across all datasets belonging to an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        return (
            _session_.query(
                func.count(UserFollowingDataset.follower_id)
            )
            .filter(
                _and_(
                    model.Package.owner_org == org_id,
                    model.Package.state == ACTIVE_STATE,
                    UserFollowingDataset.datetime >= utc_start_date,
                    UserFollowingDataset.datetime < utc_end_date,
                )
            )
            .join(model.Package, model.Package.id == UserFollowingDataset.object_id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_comments(context, data_dict):
    """
    Total count of active dataset comments across an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        return (
            _session_.query(
                func.count(distinct(Comment.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    model.Package.owner_org == org_id,
                    model.Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(model.Package, model.Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datarequests(context, data_dict):
    """
    Return the data requests assigned to an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                db.DataRequest
            )
            .filter(
                db.DataRequest.organization_id == org_id,
                db.DataRequest.open_time >= utc_start_date,
                db.DataRequest.open_time < utc_end_date,
            )
            .order_by(db.DataRequest.open_time.desc())
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequest_comments(context, data_dict):
    """
    Total count of active data request comments across an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                func.count(distinct(Comment.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    db.DataRequest.organization_id == org_id
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(db.DataRequest, db.DataRequest.id == _replace_(CommentThread.url, DATAREQUEST_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_comment_followers(context, data_dict):
    """
    Number of dataset comment followers at an organization level
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                # We want to count a user each time they follow a comment thread, not just unique user IDs
                func.count(distinct(tuple_(
                    CommentNotificationRecipient.user_id, CommentNotificationRecipient.thread_id)))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    model.Package.owner_org == org_id,
                    model.Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.id == CommentNotificationRecipient.thread_id)
            .join(Comment)
            .join(model.Package, model.Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datasets_min_one_comment_follower(context, data_dict):
    """
    Number of Datasets with at least one comment follower
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        return (
            _session_.query(
                func.count(distinct(model.Package.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    model.Package.owner_org == org_id,
                    model.Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.url == func.concat(DATASET_PREFIX, model.Package.name))
            .join(CommentNotificationRecipient, CommentNotificationRecipient.thread_id == CommentThread.id)
            # Don't need JOIN ON clause - `comment` table has `comment_thread`.`id` FK
            .join(Comment)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def datarequests_min_one_comment_follower(context, data_dict):
    """
    Number of Data Requests across an organisation with at least one comment follower
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                func.count(distinct(db.DataRequest.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    db.DataRequest.organization_id == org_id
                )
            )
            .join(CommentThread, CommentThread.url == func.concat(DATAREQUEST_PREFIX, db.DataRequest.id))
            .join(CommentNotificationRecipient, CommentNotificationRecipient.thread_id == CommentThread.id)
            .join(Comment, Comment.thread_id == CommentThread.id)
        ).scalar()

    except Exception as e:
        log.error(str(e))


def dataset_comments_no_replies_after_x_days(context, data_dict):
    """
    Dataset comments that have no replies whatsoever, and it has been > 10 days since the comment was created
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_reply_expected_by_date = data_dict.get(
        'utc_reply_expected_by_date', None)

    check_org_access(org_id, context=context)

    comment_reply = aliased(Comment, name='comment_reply')
    try:
        comments = (
            _session_.query(
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date.label("comment_creation_date"),
                Comment.subject,
                model.User.name.label('username'),
                CommentThread.url,
                model.Package.name.label("package_name"),
                comment_reply.parent_id,
                comment_reply.creation_date.label(
                    "comment_reply_creation_date"),
                comment_reply.comment,
                model.Package.title
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.parent_id.is_(None),
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_reply_expected_by_date,
                    Comment.state == ACTIVE_STATE,
                    model.Package.owner_org == org_id,
                    model.Package.state == ACTIVE_STATE,
                    comment_reply.id.is_(None)
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(model.User, Comment.user_id == model.User.id)
            .join(model.Package, model.Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id),
            )
            .order_by(Comment.creation_date.desc())
        ).all()

        comments_to_show = []
        for comment in comments:
            try:
                check_user_access('create_dataset', {"user": comment.username})
                # User has editor, admin or sysadmin access to a organisation
            except NotAuthorized:
                # User is only a member of a organisation or has no organisation access
                # Add user comment
                comments_to_show.append(comment)
                continue
        return comments_to_show

    except Exception as e:
        log.error(str(e))


def datarequests_no_replies_after_x_days(context, data_dict):
    """
    Data request comments that have no replies whatsoever, and it has been > 10 days since the comment was created
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_reply_expected_by_date = data_dict.get(
        'utc_reply_expected_by_date', None)

    check_org_access(org_id, context=context)

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        if not db.DataRequest:
            db.init_db(model)
        comments = (
            _session_.query(
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date,
                Comment.subject,
                model.User.name.label('username'),
                CommentThread.url,
                db.DataRequest.id.label("datarequest_id"),
                db.DataRequest.title,
                db.DataRequest.open_time,
                comment_reply.parent_id,
                comment_reply.creation_date,
                comment_reply.comment
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATAREQUEST_LIKE),
                    Comment.parent_id.is_(None),
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_reply_expected_by_date,
                    Comment.state == ACTIVE_STATE,
                    db.DataRequest.organization_id == org_id,
                    comment_reply.id.is_(None)
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(model.User, Comment.user_id == model.User.id)
            .join(db.DataRequest, db.DataRequest.id == _replace_(CommentThread.url, DATAREQUEST_PREFIX, ''))
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id)
            )
            .order_by(Comment.creation_date.desc())
        ).all()

        comments_to_show = []
        for comment in comments:
            try:
                check_user_access('create_dataset', {"user": comment.username})
                # User has editor, admin or sysadmin access to a organisation
            except NotAuthorized:
                # User is only a member of a organisation or has no organisation access
                # Add user comment
                comments_to_show.append(comment)
                continue
        return comments_to_show

    except Exception as e:
        log.error(str(e))


def open_datarequests_no_comments_after_x_days(context, data_dict):
    """
    Data requests that have no comments whatsoever, and it has
    been > 10 days since the data request was opened.
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_reply_expected_by_date = data_dict.get(
        'utc_reply_expected_by_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                db.DataRequest.id,
                db.DataRequest.title,
                db.DataRequest.open_time,
                CommentThread.url,
            )
            .filter(
                _and_(
                    db.DataRequest.organization_id == org_id,
                    db.DataRequest.closed.is_(False),
                    db.DataRequest.open_time >= utc_start_date,
                    db.DataRequest.open_time < utc_reply_expected_by_date,
                    Comment.id.is_(None)
                )
            )
            .outerjoin(CommentThread, CommentThread.url == func.concat(DATAREQUEST_PREFIX, db.DataRequest.id))
            .outerjoin(Comment, Comment.thread_id == CommentThread.id)
            .order_by(db.DataRequest.open_time.desc())
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequests_open_after_x_days(context, data_dict):
    """
    Data requests that have no comments whatsoever, and it has
    been > 10 days since the data request was opened.
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_expected_closure_date = data_dict.get(
        'utc_expected_closure_date', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                db.DataRequest.id,
                db.DataRequest.title,
                db.DataRequest.open_time,
            )
            .filter(
                _and_(
                    db.DataRequest.organization_id == org_id,
                    db.DataRequest.closed.is_(False),
                    db.DataRequest.open_time >= utc_start_date,
                    db.DataRequest.open_time < utc_expected_closure_date
                )
            )
            .order_by(db.DataRequest.open_time.desc())
        ).all()

    except Exception as e:
        log.error(str(e))


def datarequests_for_circumstance(context, data_dict):
    org_id = data_dict.get('org_id', None)
    utc_start_date = data_dict.get('utc_start_date', None)
    utc_end_date = data_dict.get('utc_end_date', None)
    circumstance = data_dict.get('circumstance', None)

    check_org_access(org_id, context=context)

    try:
        if not db.DataRequest:
            db.init_db(model)
        return (
            _session_.query(
                db.DataRequest
            )
            .filter(
                db.DataRequest.organization_id == org_id,
                db.DataRequest.close_circumstance == circumstance,
                db.DataRequest.open_time >= utc_start_date,
                db.DataRequest.open_time < utc_end_date,
                db.DataRequest.closed.is_(True)
            )
            .order_by(db.DataRequest.close_time.desc())
        ).all()

    except Exception as e:
        log.error(str(e))


def comments_no_replies_after_x_days(context, data_dict):
    """
    Comments that have no replies whatsoever, and it has been > X days since the comment was created
    This action is used for highlighting such comments on the comments page for the given URL
    There is no date range for this query - it is simply X days from the current date (in UTC)
    :param context:
    :param data_dict:
    :return:
    """
    thread_url = data_dict.get('thread_url', None)

    ckan_timezone = config.get('ckan.display_timezone', None)

    # Comment.creation_date is stored as UTC without timezone
    # We need to check for any comments whose creation date is earlier than
    # NOW, minus the number of days a reply is expected by (in UTC)
    today = datetime.now(pytz.timezone(ckan_timezone))

    days_to_reply = timedelta(days=constants.COMMENT_NO_REPLY_MAX_DAYS)

    x_days_from_today = today - days_to_reply

    utc_x_days_from_today = x_days_from_today.astimezone(pytz.timezone('UTC'))

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        return (
            _session_.query(
                CommentThread.url,
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date,
            )
            .filter(
                _and_(
                    CommentThread.url == thread_url,
                    Comment.parent_id.is_(None),
                    Comment.creation_date < utc_x_days_from_today,
                    Comment.state == ACTIVE_STATE,
                    comment_reply.id.is_(None)
                )
            )
            .join(Comment)
            .outerjoin(
                (comment_reply, Comment.id == comment_reply.parent_id)
            )
            .order_by(Comment.creation_date.desc())
        ).all()

    except Exception as e:
        log.error(str(e))


def de_identified_datasets(context, data_dict):
    """
    Returns the datasets that have de-identified data for an organisation
    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)
    org_id, is_org_list = _authorised_orgs(data_dict, context)

    try:
        query = (
            _active_package_query(org_id, is_org_list, return_count_only)
            .join(model.PackageExtra)
            .filter(model.PackageExtra.key == 'de_identified_data')
            .filter(model.PackageExtra.value == 'YES')
            .filter(model.PackageExtra.state == ACTIVE_STATE)
        )

        return _query_result(query, is_org_list, return_count_only)
    except Exception as e:
        log.error(str(e))


def de_identified_datasets_no_schema(context, data_dict):
    """
    Returns the datasets that have de-identified data for an organisation
    and missing default_schema

    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)

    count_from_date = h.date_str_to_datetime(
        data_dict.get('count_from', helpers.get_deidentified_count_from_date()))

    org_id, is_org_list = _authorised_orgs(data_dict, context)

    extras = model.PackageExtra
    de_identified = aliased(extras)
    data_last_updated = aliased(extras)

    sub_query = _session_.query(extras).filter(
        and_(
            extras.package_id == model.Package.id,
            extras.key == 'default_data_schema',
            extras.value != ''
        ))

    query = (
        _active_package_query(org_id, is_org_list, return_count_only)
        .join(de_identified)
        .join(data_last_updated)
        .filter(~sub_query.exists())
        .filter(and_(
            de_identified.key == 'de_identified_data',
            de_identified.value == 'YES',
            de_identified.state == ACTIVE_STATE
        ))
        .filter(and_(
            data_last_updated.key == 'data_last_updated',
            data_last_updated.value > count_from_date.isoformat()
        ))
    )

    return _query_result(query, is_org_list, return_count_only)


def overdue_datasets(context, data_dict):
    """
    Returns the datasets that are over due for an organisation
    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)
    org_id, is_org_list = _authorised_orgs(data_dict, context)

    try:
        # next_update_due is stored as display timezone without timezone as isoformat
        today = datetime.now(h.get_display_timezone()).date().isoformat()
        # We need to check for any datasets whose next_update_due is earlier than today
        query = (
            _active_package_query(org_id, is_org_list, return_count_only)
            .join(model.PackageExtra)
            .filter(model.PackageExtra.key == 'next_update_due')
            .filter(model.PackageExtra.value <= today)
            .filter(model.PackageExtra.state == ACTIVE_STATE)
        )

        return _query_result(query, is_org_list, return_count_only)
    except Exception as e:
        log.error(str(e))


def datasets_no_groups(context, data_dict):
    """
    Returns the datasets that have no groups
    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)
    org_id, is_org_list = _authorised_orgs(data_dict, context)
    try:
        sub_query = (_session_.query(model.Group.id)
                     .join(model.Member, model.Group.id == model.Member.group_id)
                     .filter(model.Member.table_name == 'package')
                     .filter(model.Member.state == ACTIVE_STATE)
                     .filter(model.Package.id == model.Member.table_id)
                     .filter(model.Group.type == 'group')
                     )

        query = (
            _active_package_query(org_id, is_org_list, return_count_only)
            .filter(~sub_query.exists())
        )

        return _query_result(query, is_org_list, return_count_only)
    except Exception as e:
        log.error(str(e))


def datasets_no_tags(context, data_dict):
    """
    Returns the datasets that have no tags
    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)
    org_id, is_org_list = _authorised_orgs(data_dict, context)
    try:
        sub_query = (_session_.query(model.PackageTag.package_id)
                     .join(model.Tag)
                     .filter(model.PackageTag.tag_id == model.Tag.id)
                     .filter(model.PackageTag.package_id == model.Package.id)
                     .filter(model.PackageTag.state == ACTIVE_STATE)
                     )

        query = (
            _active_package_query(org_id, is_org_list, return_count_only)
            .filter(~sub_query.exists())
        )

        return _query_result(query, is_org_list, return_count_only)
    except Exception as e:
        log.error(str(e))


def resources_pending_privacy_assessment(context, data_dict):
    """
    Returns the datasets that have resource with pending privacy_assessment

    :param context:
    :param data_dict:
    :return:
    """
    return_count_only = data_dict.get('return_count_only', False)
    org_id, is_org_list = _authorised_orgs(data_dict, context)

    ilike = '%"{}": "{}"%'.format(FIELD_REQUEST_ASSESS, YES)
    if return_count_only and is_org_list:
        query = _session_.query(model.Package.owner_org, func.count(model.Package.id)) \
            .join(model.Resource) \
            .group_by(model.Package.owner_org)
    else:
        query = _session_.query(model.Resource).join(model.Package)
    query = (
        query.filter(model.Package.owner_org.in_(org_id))
        .filter(model.Package.id == model.Resource.package_id)
        .filter(model.Package.state == ACTIVE_STATE)
        .filter(model.Resource.extras.ilike(ilike))
    )

    return _query_result(query, is_org_list, return_count_only)
