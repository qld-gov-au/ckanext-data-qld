import datetime as dt
import json

import logging

from ckan.lib.base import config

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
    return config.get('ckanext.dataqld.update_frequencies')


def recalculate_due_date(update_frequency, update_due=None):
    today = dt.datetime.utcnow().date()
    current_date = dt.datetime.strptime(update_due, '%Y-%m-%d').date()
    if update_due is not None and not current_date < today:
        return update_due

    days = update_frequencies.get(update_frequency)
    due_date = today + dt.timedelta(days=days)

    return due_date.strftime('%Y-%m-%d')
