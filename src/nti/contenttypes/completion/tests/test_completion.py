#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from datetime import datetime

from zope import interface
from zope import component

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.completion import CompletedItem

from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import ICompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer


@interface.implementer(IPrincipal)
class MockUser(object):

    def __init__(self, username):
        self.id = self.title = self.description = username


@interface.implementer(ICompletableItem)
class MockCompletableItem(object):

    def __init__(self, ntiid):
        self.ntiid = ntiid


@interface.implementer(ICompletionContext, IAttributeAnnotatable)
class MockCompletionContext(object):
    pass


class TestCompletion(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_adapters(self):
        user1 = MockUser(u'user1')
        user2 = MockUser(u'user2')
        completion_context = MockCompletionContext()
        assert_that(completion_context, validly_provides(ICompletionContext))

        completable_container = ICompletableItemContainer(completion_context)
        assert_that(completable_container, not_none())
        assert_that(completable_container, validly_provides(ICompletableItemContainer))

        completed_container = ICompletedItemContainer(completion_context)
        assert_that(completed_container, not_none())
        assert_that(completed_container, validly_provides(ICompletedItemContainer))

        user_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container, not_none())
        assert_that(user_container, validly_provides(IPrincipalCompletedItemContainer))
        user_container_dupe = component.queryMultiAdapter((user1, completion_context),
                                                          IPrincipalCompletedItemContainer)
        assert_that(user_container, is_(user_container_dupe))

        user_container2 = component.queryMultiAdapter((user2, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container2, is_not(user_container))

    def test_completion(self):
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        completable1 = MockCompletableItem('completable1')
        completable2 = MockCompletableItem('completable2')

        completion_context = MockCompletionContext()

        completable_container = ICompletableItemContainer(completion_context)
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(0))

        completed_container = ICompletedItemContainer(completion_context)
        assert_that(completed_container, not_none())
        assert_that(completed_container, has_length(0))

        user_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container, not_none())

        completed_item1 = CompletedItem(user1, completable1, now)
        user_container.add_completed_item(completed_item1)
        assert_that(completed_item1, validly_provides(ICompletedItem))
        assert_that(completed_item1, verifiably_provides(ICompletedItem))
