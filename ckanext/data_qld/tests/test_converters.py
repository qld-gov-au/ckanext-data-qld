# encoding: utf-8
"""Unit tests for ckan/logic/converters.py.

"""
import six
from ckanext.data_qld.converters import filesize_converter


def test_filesize_converter():
    test_cases = {' , ': None,
                  ' ': None,
                  '': None,
                  None: None,
                  '2 kb': 2048,
                  1024: 1024,
                  '1024, ': 1024,
                  }
    for key, value in six.iteritems(test_cases):
        assert value == filesize_converter(key, {})
