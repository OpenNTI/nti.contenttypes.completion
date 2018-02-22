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

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from zope import interface

from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent

from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer

from nti.coremetadata.interfaces import IUser


class TestEvents(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_progress_updated_event(self):

        @interface.implementer(IUser)
        class FakeUser(object):
            __name__ = username = u'fakeuser'

        @interface.implementer(ICompletableItem)
        class FakeCompletableItem(object):
            pass

        @interface.implementer(ICompletionContext)
        class FakeCompletionContext(object):
            pass

        event = UserProgressUpdatedEvent(FakeCompletableItem(),
                                         FakeUser(),
                                         FakeCompletionContext())
        assert_that(event, validly_provides(IUserProgressUpdatedEvent))
        assert_that(event, verifiably_provides(IUserProgressUpdatedEvent))
        assert_that(event,
                    has_properties('object', is_not(none()),
                                   'user', is_not(none()),
                                   'context', is_not(none())))
