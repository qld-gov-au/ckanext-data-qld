# encoding: utf-8

import ckan.plugins.toolkit as tk

ValidationError = tk.ValidationError
_ = tk._


def resource_visibility(value):
    """
    Set to default value if missing

    """
    return validate_value(value, "TRUE", ["TRUE", "FALSE"], 'resource visibility')


def governance_acknowledgement(value):
    """
    Set to default value if missing
    """
    return validate_value(value, "NO", ["YES", "NO"], 'governance acknowledgement')


def de_identified_data(value):
    """
    Set to default value if missing
    """
    return validate_value(value, "NO", ["YES", "NO"], 'de-identified data')


def request_privacy_assessment(value):
    """
    Set to default value if missing
    """
    return validate_value(value, "", ["YES", "NO"], 'request privacy assessment')


def validate_value(value, default_value, valid_values, field):
    if not value:
        return default_value
    if value not in valid_values:
        raise ValidationError(_('Invalid {field} value. It must be {valid_values}.'.format(field=field, valid_values=" or ".join(valid_values))))
    return value
