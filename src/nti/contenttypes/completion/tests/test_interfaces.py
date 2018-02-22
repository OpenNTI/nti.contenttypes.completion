#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import none
from hamcrest import is_not
from hamcrest import assert_that
from hamcrest import has_properties

import unittest

import fudge

from zope.dottedname import resolve as dottedname


class TestInterfaces(unittest.TestCase):

    def test_import_interfaces(self):
        dottedname.resolve('nti.contenttypes.completion.interfaces')

    def test_events(self):
        from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent
        event = UserProgressUpdatedEvent(fudge.Fake(),
                                         fudge.Fake(),
                                         fudge.Fake())
        assert_that(event,
                    has_properties('object', is_not(none()),
                                   'user', is_not(none()),
                                   'context', is_not(none())))
