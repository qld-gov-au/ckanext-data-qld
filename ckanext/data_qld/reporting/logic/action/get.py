# encoding: utf-8

from ckan import model
import logging
import sqlalchemy
import pytz

from ckan.model.follower import UserFollowingDataset, UserFollowingGroup
from ckan.model.package import Package
from ckan.model.group import Group
from ckan.model.user import User
from ckan.model.package_extra import PackageExtra
from ckanext.ytp.comments.model import Comment, CommentThread
from ckanext.ytp.comments.notification_models import CommentNotificationRecipient
from sqlalchemy import func, distinct, tuple_
from sqlalchemy.orm import aliased
from ckanext.data_qld.reporting import constants
from ckanext.data_qld.reporting.helpers import helpers
from ckanext.datarequests import db
from datetime import datetime, timedelta
from ckantoolkit import config, NotAuthorized, h

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

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(UserFollowingGroup.follower_id)
            )
            .filter(
                _and_(
                    Group.id == org_id,
                    UserFollowingGroup.datetime >= utc_start_date,
                    UserFollowingGroup.datetime < utc_end_date,
                )
            )
            .join(Group, Group.id == UserFollowingGroup.object_id)
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

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(UserFollowingDataset.follower_id)
            )
            .filter(
                _and_(
                    Package.owner_org == org_id,
                    Package.state == ACTIVE_STATE,
                    UserFollowingDataset.datetime >= utc_start_date,
                    UserFollowingDataset.datetime < utc_end_date,
                )
            )
            .join(Package, Package.id == UserFollowingDataset.object_id)
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

    check_org_access(org_id)

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
                    Package.owner_org == org_id,
                    Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
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

    check_org_access(org_id)

    try:
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

    check_org_access(org_id)

    try:
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

    check_org_access(org_id)

    try:
        db.init_db(model)
        return (
            _session_.query(
                # We want to count a user each time they follow a comment thread, not just unique user IDs
                func.count(distinct(tuple_(CommentNotificationRecipient.user_id, CommentNotificationRecipient.thread_id)))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    Package.owner_org == org_id,
                    Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.id == CommentNotificationRecipient.thread_id)
            .join(Comment)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
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

    check_org_access(org_id)

    try:
        return (
            _session_.query(
                func.count(distinct(Package.id))
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.state == ACTIVE_STATE,
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_end_date,
                    Package.owner_org == org_id,
                    Package.state == ACTIVE_STATE
                )
            )
            .join(CommentThread, CommentThread.url == func.concat(DATASET_PREFIX, Package.name))
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

    check_org_access(org_id)

    try:
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
    utc_reply_expected_by_date = data_dict.get('utc_reply_expected_by_date', None)

    check_org_access(org_id)

    comment_reply = aliased(Comment, name='comment_reply')
    try:
        comments = (
            _session_.query(
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date.label("comment_creation_date"),
                Comment.subject,
                User.name.label('username'),
                CommentThread.url,
                Package.name.label("package_name"),
                comment_reply.parent_id,
                comment_reply.creation_date.label("comment_reply_creation_date"),
                comment_reply.comment,
                Package.title
            )
            .filter(
                _and_(
                    CommentThread.url.like(DATASET_LIKE),
                    Comment.parent_id.is_(None),
                    Comment.creation_date >= utc_start_date,
                    Comment.creation_date < utc_reply_expected_by_date,
                    Comment.state == ACTIVE_STATE,
                    Package.owner_org == org_id,
                    Package.state == ACTIVE_STATE,
                    comment_reply.id.is_(None)
                )
            )
            .join(CommentThread, CommentThread.id == Comment.thread_id)
            .join(User, Comment.user_id == User.id)
            .join(Package, Package.name == _replace_(CommentThread.url, DATASET_PREFIX, ''))
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
    utc_reply_expected_by_date = data_dict.get('utc_reply_expected_by_date', None)

    check_org_access(org_id)

    comment_reply = aliased(Comment, name='comment_reply')

    try:
        db.init_db(model)
        comments = (
            _session_.query(
                Comment.id.label("comment_id"),
                Comment.parent_id,
                Comment.creation_date,
                Comment.subject,
                User.name.label('username'),
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
            .join(User, Comment.user_id == User.id)
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
    utc_reply_expected_by_date = data_dict.get('utc_reply_expected_by_date', None)

    check_org_access(org_id)

    try:
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
    utc_expected_closure_date = data_dict.get('utc_expected_closure_date', None)

    check_org_access(org_id)

    try:
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

    check_org_access(org_id)

    try:
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
    org_id = data_dict.get('org_id', None)
    return_count_only = data_dict.get('return_count_only', False)
    permission = data_dict.get('permission', 'admin')
    check_org_access(org_id, permission)

    try:
        query = (
            _session_.query(Package)
            .join(model.PackageExtra)
            .filter(Package.owner_org == org_id)
            .filter(Package.state == ACTIVE_STATE)
            .filter(PackageExtra.key == 'de_identified_data')
            .filter(PackageExtra.value == 'YES')
            .filter(PackageExtra.state == ACTIVE_STATE)
        )

        if return_count_only:
            datasets = query.count()
        else:
            datasets = query.all()

        return datasets
    except Exception as e:
        log.error(str(e))


def overdue_datasets(context, data_dict):
    """
    Returns the datasets that are over due for an organisation
    :param context:
    :param data_dict:
    :return:
    """
    org_id = data_dict.get('org_id', None)
    return_count_only = data_dict.get('return_count_only', False)
    permission = data_dict.get('permission', 'admin')
    check_org_access(org_id, permission)

    try:
        # next_update_due is stored as display timezone without timezone as isoformat
        today = datetime.now(h.get_display_timezone()).date().isoformat()
        # We need to check for any datasets whose next_update_due is earlier than today
        query = (
            _session_.query(Package)
            .join(model.PackageExtra)
            .filter(Package.owner_org == org_id)
            .filter(Package.state == ACTIVE_STATE)
            .filter(PackageExtra.key == 'next_update_due')
            .filter(PackageExtra.value <= today)
            .filter(PackageExtra.state == ACTIVE_STATE)
        )

        if return_count_only:
            datasets = query.count()
        else:
            datasets = query.all()
        return datasets
    except Exception as e:
        log.error(str(e))
