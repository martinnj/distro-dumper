""" Testing validators. """

import pytest

from distrodumper import validation

@pytest.mark.parametrize("val,atoms,expected",[
    ("mystr",         ["mystr", "yourstr"], True),
    ("mystr,mystr",   ["mystr", "yourstr"], True),
    ("mystr,yourstr", ["mystr", "yourstr"], True),
    ("yourstr",       ["mystr", "yourstr"], True),
    ("mystr",         ["yourstr"], False),
    ("",              ["yourstr"], False),
    (1,               ["1"], False),
    (1.1,             ["1"], False),
    (True,            ["True"], False),
])
def test_atomic_csv(val, atoms, expected):
    """ Test the atomic csv string validator. """
    assert validation.is_atomic_csv(val, atoms) == expected


@pytest.mark.parametrize("val,expected",[
    ("True",   True),
    ("true",   True),
    ("tRuE",   True),
    ("False",  True),
    ("false",  True),
    ("untrue", False),
    (" true",  False),
    ("true ",  False),
    (True,     False),
    (False,    False),
    (1,        False),
    (1.1,      False),
])
def test_bool_string(val, expected):
    """ Test the bool string validator. """
    assert validation.is_bool_string(val) == expected


@pytest.mark.parametrize("val,expected",[
    ("abc", True),
    ("1",   True),
    (" ",   True),
    ("",    False),
    (True,  False),
    (False, False),
    (1,     False),
    (1.1,   False),
])
def test_is_non_empty_string(val, expected):
    """ Test the non-empty string validator. """
    assert validation.is_non_empty_string(val) == expected


@pytest.mark.parametrize("val,expected",[
    ("1", True),
    ("11231", True),
    ("0", False),
    (1, True),
    (11231, True),
    (0, False),
    (1.1, False),
    (True, False),
    (False, False),
])
def test_is_non_zero_int(val, expected):
    """ Test the non-zero int validator. """
    assert validation.is_non_zero_int(val) == expected
