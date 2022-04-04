# encoding: utf-8

import ckan.plugins.toolkit as tk

StopOnError = tk.StopOnError
_ = tk._


def resource_visibility(value):
    """
    Set to default value if missing

    """
    if not value:
        return "TRUE"
    if value not in ["TRUE", "FALSE"]:
        raise StopOnError(_('Invalid resource visibility value. It must be TRUE or FALSE.'))
    return value


def governance_acknowledgement(value):
    """
    Set to default value if missing
    """
    if not value:
        return "NO"
    if value not in ["YES", "NO"]:
        raise StopOnError(_('Invalid governance acknowledgement value. It must be YES or NO.'))
    return value
