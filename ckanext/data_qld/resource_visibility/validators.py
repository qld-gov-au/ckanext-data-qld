# encoding: utf-8

import ckan.plugins.toolkit as tk

ValidationError = tk.ValidationError
_ = tk._


def resource_visibility(value):
    """
    Set to default value if missing

    """
    if not value:
        return "TRUE"
    if value not in ["TRUE", "FALSE"]:
        raise ValidationError(_('Invalid resource visibility value. It must be TRUE or FALSE.'))
    return value


def governance_acknowledgement(value):
    """
    Set to default value if missing
    """
    if not value:
        return "NO"
    if value not in ["YES", "NO"]:
        raise ValidationError(_('Invalid governance acknowledgement value. It must be YES or NO.'))
    return value


def de_identified_data(value):
    """
    Set to default value if missing
    """
    if not value:
        return "NO"
    if value not in ["YES", "NO"]:
        raise ValidationError(_('Invalid de-identified data value. It must be YES or NO.'))
    return value
