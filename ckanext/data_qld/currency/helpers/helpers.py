import datetime as dt

update_frequencies = {
    "monthly": 30,
    "quarterly": 91,
    "semiannually": 182,
    "annually": 365
}


def recalculate_due_date(update_frequency, update_due=None):
    # if update_due is not None:
    #     return update_due

    return dt.date.today() +\
        dt.timedelta(days=update_frequencies.get(update_frequency))
