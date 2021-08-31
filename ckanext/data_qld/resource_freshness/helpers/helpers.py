import datetime as dt
import json
import logging

from ckan.plugins.toolkit import get_validator
from ckan.lib.base import config
from ckanext.data_qld import helpers as h

log = logging.getLogger(__name__)

update_frequencies = {
    "monthly": 30,
    "quarterly": 91,
    "semiannually": 182,
    "annually": 365
}


def get_update_frequencies():
    try:
        return json.loads(update_frequencies_from_config())
    except ValueError:
        log.warning('Unable to load update frequencies from config')
        return update_frequencies


def update_frequencies_from_config():
    return config.get('ckanext.resource_freshness.update_frequencies')


def recalculate_next_update_due_date(update_frequency, next_update_due=None):
    days = get_update_frequencies().get(update_frequency, 0)
    # Recalcualte the next_update_due if its not none
    if next_update_due is not None:
        next_update_due = get_validator('isodate')(next_update_due, {})
        due_date = next_update_due.date() + dt.timedelta(days=days)
    else:
        # Recalculate the UpdateDue date if its None
        due_date = dt.datetime.utcnow().date() + dt.timedelta(days=days)

    return due_date


def process_next_update_due(data_dict):
    if not h.user_has_admin_access(True):
        if 'next_update_due' in data_dict:
            del data_dict['next_update_due']
        for res in data_dict.get('resources', []):
            if 'nature_of_change' in res:
                del res['nature_of_change']


def process_nature_of_change(resource_dict):
    if not h.user_has_admin_access(True) and 'nature_of_change' in resource_dict:
        del resource_dict['nature_of_change']
