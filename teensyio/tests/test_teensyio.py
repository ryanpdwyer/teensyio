# -*- coding: utf-8 -*-
"""
Tests for `teensyio` module.
"""
import unittest
import itertools
from StringIO import StringIO
from nose.tools import ok_

from teensyio import arbitrary_line_split

def test_arbitrary_line_split():
    text = "100 100\n200 200\n300 300\n"
    expected = ['100 100', '200 200', '300 300']
    for i in xrange(1, len(text)):
        buf = StringIO(text)
        # make buf mimic a serial port object
        buf.inWaiting = lambda : i
        gen = arbitrary_line_split(buf, return_if_empty=True)
        # See http://stackoverflow.com/a/406199/2823213
        out = list(itertools.chain.from_iterable(gen))
        ok_(out, expected)




class TestTeensyio(unittest.TestCase):

    def setUp(self):
        pass

    def test_something(self):
        pass

    def tearDown(self):
        pass
