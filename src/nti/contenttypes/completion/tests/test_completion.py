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

from nose.tools import assert_raises

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
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer

from nti.wref.interfaces import IWeakRef


@interface.implementer(IPrincipal)
class MockUser(object):

    def __init__(self, username):
        self.id = self.title = self.description = username


@interface.implementer(IWeakRef)
class _IdentityWref(object):

    def __init__(self, gbe):
        self.gbe = gbe

    def __call__(self):
        return self.gbe

    def __eq__(self, unused_other):
        return True

    def __hash__(self):
        return 42


@interface.implementer(ICompletableItem)
class MockCompletableItem(object):

    def __init__(self, ntiid):
        self.ntiid = ntiid

    def __conform__(self, unused_iface):
        return _IdentityWref(self)


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

        policy_container = ICompletionContextCompletionPolicyContainer(completion_context)
        assert_that(policy_container, not_none())
        assert_that(policy_container, validly_provides(ICompletionContextCompletionPolicyContainer))
        assert_that(policy_container.context_policy, none())

    def test_completed(self):
        """
        Test completed item storage, access, and removal.
        """
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        user2 = MockUser(u'user2')
        completable1 = MockCompletableItem('completable1')
        completable2 = MockCompletableItem('completable2')
        completion_context = MockCompletionContext()

        # Base cases
        completed_container = ICompletedItemContainer(completion_context)
        assert_that(completed_container, not_none())
        assert_that(completed_container, has_length(0))
        assert_that(completed_container.get_completed_item_count(completable1), is_(0))
        assert_that(completed_container.remove_item(completable1), is_(0))

        user_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container, not_none())
        assert_that(user_container.Principal, is_(user1))
        assert_that(user_container.get_completed_item_count(), is_(0))
        assert_that(user_container.get_completed_item(completable1), none())
        assert_that(user_container.remove_item(completable1), is_(False))

        completed_item1 = CompletedItem(Principal=user1, Item=completable1, CompletedDate=now)
        user_container.add_completed_item(completed_item1)
        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1), is_(completed_item1))
        assert_that(completed_item1, validly_provides(ICompletedItem))
        assert_that(completed_item1, verifiably_provides(ICompletedItem))
        assert_that(completed_item1.Item, is_(completable1))
        assert_that(completed_item1._item, not_none())

        # Idempotent
        user_container.add_completed_item(completed_item1)
        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1), is_(completed_item1))


        # Second user
        user_container2 = component.queryMultiAdapter((user2, completion_context),
                                                      IPrincipalCompletedItemContainer)

        with assert_raises(AssertionError):
            # Add to incorrect container
            user_container2.add_completed_item(completed_item1)

        # Multiple
        completed_item2 = CompletedItem(Principal=user1, Item=completable2, CompletedDate=now)
        user_container.add_completed_item(completed_item2)
        assert_that(user_container.get_completed_item_count(), is_(2))

        completed_item3 = CompletedItem(Principal=user2, Item=completable2, CompletedDate=now)
        user_container2.add_completed_item(completed_item3)
        assert_that(user_container2.get_completed_item_count(), is_(1))

        # Validate counts
        assert_that(completed_container.get_completed_item_count(completable1), is_(1))
        assert_that(completed_container.get_completed_item_count(completable2), is_(2))

        # Removal
        remove_count = completed_container.remove_item(completable1)
        assert_that(remove_count, is_(1))
        assert_that(completed_container.get_completed_item_count(completable1), is_(0))
        assert_that(completed_container.get_completed_item_count(completable2), is_(2))

        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1), none())

        assert_that(user_container2.get_completed_item_count(), is_(1))
        assert_that(user_container2.get_completed_item(completable1), none())

        # Removal of second item
        remove_count = completed_container.remove_item(completable2)
        assert_that(remove_count, is_(2))
        assert_that(completed_container.get_completed_item_count(completable1), is_(0))
        assert_that(completed_container.get_completed_item_count(completable2), is_(0))

        assert_that(user_container.get_completed_item_count(), is_(0))
        assert_that(user_container.get_completed_item(completable2), none())

        assert_that(user_container2.get_completed_item_count(), is_(0))
        assert_that(user_container2.get_completed_item(completable2), none())

    def test_completable(self):
        """
        Test completable item references, functions.
        """
        completable1 = MockCompletableItem('completable1')
        completable2 = MockCompletableItem('completable2')
        completable3 = MockCompletableItem('completable3')

        completion_context = MockCompletionContext()

        # Base cases
        completable_container = ICompletableItemContainer(completion_context)
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(0))

        # Add items (removing items that do not exist
        completable_container.add_required_item(completable1)
        assert_that(completable_container.remove_optional_item(completable2), is_(False))
        assert_that(completable_container.remove_required_item(completable3), is_(False))
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(1))

        completable_container.add_required_item(completable2)
        assert_that(completable_container.remove_optional_item(completable2), is_(False))
        assert_that(completable_container.remove_required_item(completable3), is_(False))
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(2))

        completable_container.add_optional_item(completable3)
        assert_that(completable_container.remove_optional_item(completable2), is_(False))
        assert_that(completable_container.remove_required_item(completable3), is_(False))
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(2))

        assert_that(completable_container.is_item_required(completable1),
                    is_(True))
        assert_that(completable_container.is_item_required(completable2),
                    is_(True))
        assert_that(completable_container.is_item_required(completable3),
                    is_(False))

        assert_that(completable_container.is_item_optional(completable1),
                    is_(False))
        assert_that(completable_container.is_item_optional(completable2),
                    is_(False))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(True))

        # Remove items
        assert_that(completable_container.remove_required_item(completable1), is_(True))
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(1))

        assert_that(completable_container.is_item_required(completable1),
                    is_(False))
        assert_that(completable_container.is_item_required(completable2),
                    is_(True))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(True))

        assert_that(completable_container.remove_required_item(completable1), is_(False))
        assert_that(completable_container.remove_required_item(completable2), is_(True))
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(0))

        assert_that(completable_container.is_item_required(completable1),
                    is_(False))
        assert_that(completable_container.is_item_required(completable2),
                    is_(False))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(True))

        assert_that(completable_container.remove_required_item(completable1), is_(False))
        assert_that(completable_container.remove_required_item(completable2), is_(False))
        assert_that(completable_container.remove_optional_item(completable3), is_(True))
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(0))

        assert_that(completable_container.is_item_required(completable1),
                    is_(False))
        assert_that(completable_container.is_item_required(completable2),
                    is_(False))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(False))

        # Transfer from optional -> required (and reverse)
        completable_container.add_required_item(completable2)
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(1))
        completable_container.add_optional_item(completable2)
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(0))
        completable_container.add_required_item(completable2)
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(1))
