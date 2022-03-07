# encoding: utf-8

import re

import ckan.lib.formatters as formatters
from ckantoolkit import Invalid


def filesize_converter(value, context):
    """Returns the converted size into bytes

    :rtype: int

    """
    value = str(value)
    # remove whitespaces
    value = re.sub(' ', '', value)
    # remove commas
    value = re.sub(',', '', value)
    value = value.upper()

    # If the size is not all digits then get size converted into bytes
    if re.search(r'^\d+$', value) is None:
        value = filesize_bytes(value)

    return value


def filesize_bytes(value):
    """Returns the converted size into bytes
        size types TERABYTES, GIGABYTES, MEGABYTES, KILOBYTES
    :rtype: int

    """
    if re.search(r'^\d*\.?\d+[A-Za-z]*$', value) is not None:
        size_type = re.search(r'[A-Za-z]+', value)
        size_number = re.search(r'\d*\.?\d*', value)

        if size_type is None or size_number is None:
            raise Invalid('Must be a valid filesize format (e.g. 123, 1.2KB, 2.5MB)')
        else:
            size_type = size_type.group().upper()
            size_number = float(size_number.group())

        if size_type == 'TB' or size_type == 'T' or size_type == 'TERABYTES' or size_type == 'TBS' or size_type == 'TIB':
            fileMultiplier = 1099511627776
        elif size_type == 'GB' or size_type == 'G' or size_type == 'GIGABYTES' or size_type == 'GIG' or size_type == 'GBS' or size_type == 'GIB':
            fileMultiplier = 1073741824
        elif size_type == 'MB' or size_type == 'M' or size_type == 'MEGABYTES' or size_type == 'MBS' or size_type == 'MIB':
            fileMultiplier = 1048576
        elif size_type == 'KB' or size_type == 'K' or size_type == 'KILOBYTES' or size_type == 'KBS' or size_type == 'KIB':
            fileMultiplier = 1024
        elif size_type == 'B' or size_type == 'BYTES' or size_type == 'BS':
            fileMultiplier = 1
        else:
            raise Invalid('Must be a valid filesize format (e.g. 123, 1.2KB, 2.5MB)')

        return int(size_number * fileMultiplier)
    else:
        raise Invalid('Must be a valid filesize format')


def filesize_formatter(size):
    """Returns a localised unicode representation of a number in bytes, MiB etc
    :rtype: string

    """
    try:
        return formatters.localised_filesize(int(size))
    except (AttributeError, ValueError):
        # already formatted or unable to run formatter
        return size
