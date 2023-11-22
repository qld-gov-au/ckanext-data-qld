# encoding: utf-8
"""Unit tests for ckan/logic/converters.py.

"""
import six
from ckanext.data_qld.converters import filesize_converter


def test_filesize_converter():
    test_cases = {'foo': 'FOO',
                  'FOO': 'FOO',
                  'foo,baz': 'FOOBAZ',
                  ' , ': None,
                  ' ': None,
                  '': None,
                  None: None,
                  1024: '1 KiB',
                  '1024': '1 KiB',
                  '1024, ': '1 KiB',
                  '1024a': '1024A',
                  }
    for key, value in six.iteritems(test_cases):
        assert value == filesize_converter(key, {})
