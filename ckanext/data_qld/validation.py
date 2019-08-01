import ckanext.scheming.helpers as sh
from ckantoolkit import missing, Invalid, _, get_validator

OneOf = get_validator('OneOf')


def scheming_validator(fn):
    """
    Decorate a validator that needs to have the scheming fields
    passed with this function. When generating navl validator lists
    the function decorated will be called passing the field
    and complete schema to produce the actual validator for each field.
    """
    fn.is_a_scheming_validator = True
    return fn


@scheming_validator
def scheming_choices(field, schema):
    """
    Require that one of the field choices values is passed.
    """
    if 'choices' in field:
        return OneOf([c['value'] for c in field['choices']])

    def validator(value):
        if value is missing or not value:
            return value
        choices = sh.scheming_field_choices(field)
        for c in choices:
            #  We want the value check to be case insensitive
            if value.upper() == c['value'].upper():
                return value
        raise Invalid(_('unexpected choice "%s"') % value)

    return validator
