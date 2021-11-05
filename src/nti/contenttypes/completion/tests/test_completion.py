#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ
from contextlib import contextmanager

from hamcrest import has_key
from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that

from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent
from nti.contenttypes.completion.interfaces import IPrincipalAwardedCompletedItemContainer

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import fudge
import unittest

from datetime import datetime

from ZODB.interfaces import IConnection

from zope import component
from zope.component import eventtesting

from zope.dublincore.interfaces import IWriteZopeDublinCore

from zope.event import notify
from zope.lifecycleevent import IObjectAddedEvent
from zope.lifecycleevent import IObjectRemovedEvent

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.completion import CompletedItem
from nti.contenttypes.completion.completion import AwardedCompletedItem

from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import IAwardedCompletedItem
from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import ICompletedItemContainer
from nti.contenttypes.completion.interfaces import IAwardedCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer
from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import UserProgressRemovedEvent

from nti.contenttypes.completion.policies import AbstractCompletableItemCompletionPolicy
from nti.contenttypes.completion.policies import CompletableItemAggregateCompletionPolicy

from nti.contenttypes.completion.tests import DSSharedConfiguringTestLayer
from nti.contenttypes.completion.tests import SharedConfiguringTestLayer

from nti.contenttypes.completion.tests.interfaces import ITestCompletableItem

from nti.contenttypes.completion.tests.test_models import MockUser
from nti.contenttypes.completion.tests.test_models import MockCompletableItem
from nti.contenttypes.completion.tests.test_models import MockCompletionContext

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

CLASS = StandardExternalFields.CLASS
ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE


class TestCompletion(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_externalization(self):
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        completable1 = MockCompletableItem('completable1')
        completed_item = CompletedItem(Principal=user1,
                                       Item=completable1,
                                       CompletedDate=now)
        ext_obj = to_external_object(completed_item)
        assert_that(ext_obj[CLASS], is_('CompletedItem'))
        assert_that(ext_obj[MIMETYPE],
                    is_('application/vnd.nextthought.completion.completeditem'))
        assert_that(ext_obj['CompletedDate'], not_none())
        assert_that(ext_obj['Success'], is_(True))

        factory = find_factory_for(ext_obj)
        assert_that(factory, none())

    def test_adapters(self):
        user1 = MockUser(u'user1')
        user2 = MockUser(u'user2')
        completion_context = MockCompletionContext()
        assert_that(completion_context, validly_provides(ICompletionContext))

        completable_container = ICompletableItemContainer(completion_context)
        assert_that(completable_container, not_none())
        assert_that(completable_container,
                    validly_provides(ICompletableItemContainer))

        completed_container = ICompletedItemContainer(completion_context)
        assert_that(completed_container, not_none())
        assert_that(completed_container,
                    validly_provides(ICompletedItemContainer))
        assert_that(IWriteZopeDublinCore(completed_container, None),
                    none())
        
        awarded_completed_container = IAwardedCompletedItemContainer(completion_context)
        assert_that(awarded_completed_container, not_none())
        assert_that(awarded_completed_container,
                    validly_provides(IAwardedCompletedItemContainer))
        assert_that(IWriteZopeDublinCore(awarded_completed_container, None),
                    none())

        user_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container, not_none())
        assert_that(user_container,
                    validly_provides(IPrincipalCompletedItemContainer))
        user_container_dupe = component.queryMultiAdapter((user1, completion_context),
                                                          IPrincipalCompletedItemContainer)
        assert_that(user_container, is_(user_container_dupe))

        user_container2 = component.queryMultiAdapter((user2, completion_context),
                                                      IPrincipalCompletedItemContainer)
        assert_that(user_container2, is_not(user_container))
        
        user_awarded_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalAwardedCompletedItemContainer)
        assert_that(user_awarded_container, not_none())
        assert_that(user_awarded_container,
                    validly_provides(IPrincipalAwardedCompletedItemContainer))
        user_awarded_container_dupe = component.queryMultiAdapter((user1, completion_context),
                                                          IPrincipalAwardedCompletedItemContainer)
        assert_that(user_awarded_container, is_(user_awarded_container_dupe))

        user_awarded_container2 = component.queryMultiAdapter((user2, completion_context),
                                                      IPrincipalAwardedCompletedItemContainer)
        assert_that(user_awarded_container2, is_not(user_awarded_container))

        policy_container = ICompletionContextCompletionPolicyContainer(completion_context)
        assert_that(policy_container, not_none())
        assert_that(policy_container,
                    validly_provides(ICompletionContextCompletionPolicyContainer))
        assert_that(policy_container.context_policy, none())

        context_policy = ICompletionContextCompletionPolicy(completion_context, None)
        assert_that(context_policy, none())

        completion_policy = CompletableItemAggregateCompletionPolicy()
        policy_container.context_policy = completion_policy
        context_policy = ICompletionContextCompletionPolicy(completion_context, None)
        assert_that(context_policy, is_(completion_policy))

        default_required = ICompletableItemDefaultRequiredPolicy(completion_context)
        assert_that(default_required, not_none())
        assert_that(default_required,
                    validly_provides(ICompletableItemDefaultRequiredPolicy))
        assert_that(default_required.mime_types, has_length(0))

        assert_that(completed_container, has_length(2))
        completed_container.clear()
        assert_that(completed_container, has_length(0))
        assert_that(user_container, has_length(0))
        assert_that(user_container2, has_length(0))

    def test_completed(self):
        """
        Test completed item storage, access, and removal.
        """
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        user2 = MockUser(u'user2')
        completable1 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable1')
        completable2 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable2')
        completion_context = MockCompletionContext()
        # pylint: disable=too-many-function-args
        # Base cases
        completed_container = ICompletedItemContainer(completion_context)
        assert_that(completed_container, not_none())
        assert_that(completed_container, has_length(0))
        assert_that(completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(completed_container.remove_item(completable1), is_(0))

        user_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalCompletedItemContainer)
        assert_that(user_container, not_none())
        assert_that(user_container.Principal, is_(user1))
        assert_that(user_container.get_completed_item_count(), is_(0))
        assert_that(user_container.get_completed_item(completable1), none())
        assert_that(user_container.remove_item(completable1), is_(False))

        completed_item1 = CompletedItem(Principal=user1,
                                        Item=completable1,
                                        CompletedDate=now)
        user_container.add_completed_item(completed_item1)
        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1),
                    is_(completed_item1))
        assert_that(completed_item1, validly_provides(ICompletedItem))
        assert_that(completed_item1, verifiably_provides(ICompletedItem))
        assert_that(completed_item1.Item, is_(completable1))
        assert_that(completed_item1._item, not_none())
        assert_that(completed_item1.item_ntiid, is_(completable1.ntiid))

        # Idempotent
        user_container.add_completed_item(completed_item1)
        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1),
                    is_(completed_item1))

        # Second user
        user_container2 = component.queryMultiAdapter((user2, completion_context),
                                                      IPrincipalCompletedItemContainer)

        with self.assertRaises(AssertionError):
            # Add to incorrect container
            user_container2.add_completed_item(completed_item1)

        # Multiple
        completed_item2 = CompletedItem(Principal=user1, Item=completable2,
                                        CompletedDate=now)
        user_container.add_completed_item(completed_item2)
        assert_that(user_container.get_completed_item_count(), is_(2))

        completed_item3 = CompletedItem(Principal=user2, Item=completable2,
                                        CompletedDate=now)
        user_container2.add_completed_item(completed_item3)
        assert_that(user_container2.get_completed_item_count(), is_(1))

        # Validate counts
        assert_that(completed_container.get_completed_item_count(completable1),
                    is_(1))
        assert_that(completed_container.get_completed_item_count(completable2),
                    is_(2))

        # Removal
        remove_count = completed_container.remove_item(completable1)
        assert_that(remove_count, is_(1))
        assert_that(completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(completed_container.get_completed_item_count(completable2),
                    is_(2))

        assert_that(user_container.get_completed_item_count(), is_(1))
        assert_that(user_container.get_completed_item(completable1), none())

        assert_that(user_container2.get_completed_item_count(), is_(1))
        assert_that(user_container2.get_completed_item(completable1), none())

        # Removal of second item
        remove_count = completed_container.remove_item(completable2)
        assert_that(remove_count, is_(2))
        assert_that(completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(completed_container.get_completed_item_count(completable2),
                    is_(0))

        assert_that(user_container.get_completed_item_count(), is_(0))
        assert_that(user_container.get_completed_item(completable2), none())

        assert_that(user_container2.get_completed_item_count(), is_(0))
        assert_that(user_container2.get_completed_item(completable2), none())
        
    def test_awarded_completed(self):
        """
        Test manually awarding completed items
        """
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        user2 = MockUser(u'user2')
        site_admin = MockUser(u'site_admin')
        completable1 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable1')
        completable2 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable2')
        completion_context = MockCompletionContext()
        # pylint: disable=too-many-function-args
        
        awarded_completed_container = IAwardedCompletedItemContainer(completion_context)
        
        assert_that(awarded_completed_container, not_none())
        assert_that(awarded_completed_container, has_length(0))
        assert_that(awarded_completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(awarded_completed_container.remove_item(completable1), is_(0))
        
        user_awarded_container = component.queryMultiAdapter((user1, completion_context),
                                                     IPrincipalAwardedCompletedItemContainer)
        
        assert_that(user_awarded_container, not_none())
        assert_that(user_awarded_container.Principal, is_(user1))
        assert_that(user_awarded_container.get_completed_item_count(), is_(0))
        assert_that(user_awarded_container.get_completed_item(completable1), none())
        assert_that(user_awarded_container.remove_item(completable1), is_(False))
        
        awarded_completed_item1 = AwardedCompletedItem(Principal=user1,
                                                       Item=completable1,
                                                       CompletedDate=now,
                                                       awarder=site_admin,
                                                       reason=u"Good Soup")
        
        user_awarded_container.add_completed_item(awarded_completed_item1)
        assert_that(user_awarded_container.get_completed_item_count(), is_(1))
        assert_that(user_awarded_container.get_completed_item(completable1),
                    is_(awarded_completed_item1))
        assert_that(awarded_completed_item1, validly_provides(IAwardedCompletedItem))
        assert_that(awarded_completed_item1, verifiably_provides(IAwardedCompletedItem))
        assert_that(awarded_completed_item1.Item, is_(completable1))
        assert_that(awarded_completed_item1._item, not_none())
        assert_that(awarded_completed_item1.item_ntiid, is_(completable1.ntiid))

        # Idempotent
        user_awarded_container.add_completed_item(awarded_completed_item1)
        assert_that(user_awarded_container.get_completed_item_count(), is_(1))
        assert_that(user_awarded_container.get_completed_item(completable1),
                    is_(awarded_completed_item1))

        # Second user
        user_awarded_container2 = component.queryMultiAdapter((user2, completion_context),
                                                      IPrincipalAwardedCompletedItemContainer)

        with self.assertRaises(AssertionError):
            # Add to incorrect container
            user_awarded_container2.add_completed_item(awarded_completed_item1)

        # Multiple
        awarded_completed_item2 = AwardedCompletedItem(Principal=user1, 
                                                       Item=completable2,
                                                       CompletedDate=now,
                                                       awarder=site_admin,
                                                       reason=u"Vanguard Override")
        user_awarded_container.add_completed_item(awarded_completed_item2)
        assert_that(user_awarded_container.get_completed_item_count(), is_(2))

        awarded_completed_item3 = AwardedCompletedItem(Principal=user2, 
                                                       Item=completable2,
                                                       CompletedDate=now,
                                                       awarder=site_admin,
                                                       reason=u"Cayde-6's Favorite")
        
        user_awarded_container2.add_completed_item(awarded_completed_item3)
        assert_that(user_awarded_container2.get_completed_item_count(), is_(1))

        # Validate counts
        assert_that(awarded_completed_container.get_completed_item_count(completable1),
                    is_(1))
        assert_that(awarded_completed_container.get_completed_item_count(completable2),
                    is_(2))

        # Removal
        remove_count = awarded_completed_container.remove_item(completable1)
        assert_that(remove_count, is_(1))
        assert_that(awarded_completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(awarded_completed_container.get_completed_item_count(completable2),
                    is_(2))

        assert_that(user_awarded_container.get_completed_item_count(), is_(1))
        assert_that(user_awarded_container.get_completed_item(completable1), none())

        assert_that(user_awarded_container2.get_completed_item_count(), is_(1))
        assert_that(user_awarded_container2.get_completed_item(completable1), none())

        # Removal of second item
        remove_count = awarded_completed_container.remove_item(completable2)
        assert_that(remove_count, is_(2))
        assert_that(awarded_completed_container.get_completed_item_count(completable1),
                    is_(0))
        assert_that(awarded_completed_container.get_completed_item_count(completable2),
                    is_(0))

        assert_that(user_awarded_container.get_completed_item_count(), is_(0))
        assert_that(user_awarded_container.get_completed_item(completable2), none())

        assert_that(user_awarded_container2.get_completed_item_count(), is_(0))
        assert_that(user_awarded_container2.get_completed_item(completable2), none())

    @fudge.patch('nti.contenttypes.completion.internalization.find_object_with_ntiid')
    def test_completable(self, mock_find_object):
        """
        Test completable item references, functions.
        """
        completable1 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable1')
        completable2 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable2')
        completable3 = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable3')

        completion_context = MockCompletionContext()
        # pylint: disable=too-many-function-args
        # Base cases
        completable_container = ICompletableItemContainer(completion_context)
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(0))

        # Add items (removing items that do not exist
        completable_container.add_required_item(completable1)
        assert_that(completable_container.get_required_keys(),
                    has_length(1))
        assert_that(completable_container.remove_optional_item(completable2),
                    is_(False))
        assert_that(completable_container.remove_required_item(completable3),
                    is_(False))
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(1))

        completable_container.add_required_item(completable2)
        assert_that(completable_container.remove_optional_item(completable2),
                    is_(False))
        assert_that(completable_container.remove_required_item(completable3),
                    is_(False))
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(2))

        completable_container.add_optional_item(completable3)
        assert_that(completable_container.get_optional_keys(),
                    has_length(1))
        assert_that(completable_container.remove_optional_item(completable2),
                    is_(False))
        assert_that(completable_container.remove_required_item(completable3),
                    is_(False))
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
        assert_that(completable_container.remove_required_item(completable1.ntiid),
                    is_(True))
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(1))

        assert_that(completable_container.is_item_required(completable1),
                    is_(False))
        assert_that(completable_container.is_item_required(completable2),
                    is_(True))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(True))

        assert_that(completable_container.remove_required_item(completable1),
                    is_(False))
        assert_that(completable_container.remove_required_item(completable2),
                    is_(True))
        assert_that(completable_container.get_optional_item_count(), is_(1))
        assert_that(completable_container.get_required_item_count(), is_(0))

        assert_that(completable_container.is_item_required(completable1),
                    is_(False))
        assert_that(completable_container.is_item_required(completable2),
                    is_(False))
        assert_that(completable_container.is_item_optional(completable3),
                    is_(True))

        assert_that(completable_container.remove_required_item(completable1),
                    is_(False))
        assert_that(completable_container.remove_required_item(completable2),
                    is_(False))
        assert_that(completable_container.remove_optional_item(completable3),
                    is_(True))
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

        # Externalization
        ext_obj = to_external_object(completable_container)
        assert_that(ext_obj[CLASS], is_('CompletableItemContainer'))
        assert_that(ext_obj[MIMETYPE],
                    is_('application/vnd.nextthought.completion.completableitemcontainer'))
        assert_that(ext_obj['required'], has_length(1))
        assert_that(ext_obj['optional'], has_length(0))

        # clear
        completable_container.clear()
        assert_that(completable_container.get_optional_item_count(), is_(0))
        assert_that(completable_container.get_required_item_count(), is_(0))

        # Cannot find object
        mock_find_object.is_callable().returns(None)
        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.get_required_keys(), has_length(0))
        assert_that(new_io.get_optional_keys(), has_length(0))

        # Found one
        mock_find_object.is_callable().returns(completable2)
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.get_required_keys(), has_length(1))
        assert_that(new_io.get_optional_keys(), has_length(0))


class TestRemoved(unittest.TestCase):

    layer = DSSharedConfiguringTestLayer

    def _static_completion_policy(self, completed_item):
        # Always returns None
        @component.adapter(ITestCompletableItem, ICompletionContext)
        class MockCompletionPolicy(AbstractCompletableItemCompletionPolicy):

            def __init__(self, *args, **kwargs):
                pass

            def is_complete(self, _progress):
                return completed_item

        return MockCompletionPolicy

    @WithMockDSTrans
    def test_completion_removed(self):
        """
        Don't fire progress updated events on "removal" success status
        hasn't changed.
        """
        completable = MockCompletableItem(u'tag:nextthought.com,2011-10:NTI-TEST-completable1')
        completable.Success = True

        completion_context = self.make_context()

        # Mark item required
        self._require_completable_for_context(completable, completion_context)

        user = IPrincipal(User.create_user(username='completion_tester'))

        # Establish progress adapter and completion policy for item that
        # will return unsuccessfully complete item
        progress_adapter = fudge.Fake('ProgressAdapter').is_callable().returns(object())
        completed_item = CompletedItem(Item=completable,
                                       Principal=user,
                                       CompletedDate=datetime.utcnow(),
                                       Success=True)
        item_completion_policy = self._static_completion_policy(completed_item=completed_item)

        # Ensure we have a successfully completed item in place
        completed_container = component.queryMultiAdapter((user, completion_context),
                                                          IPrincipalCompletedItemContainer)
        assert_that(completed_container, has_length(0))

        completed_container[completable.ntiid] = completed_item
        assert_that(completed_container, has_key(completable.ntiid))

        # Firing removal notification
        eventtesting.clearEvents()
        with _registered_adapter(progress_adapter,
                                 required=(IPrincipal, ITestCompletableItem, ICompletionContext),
                                 provided=IProgress):
            with _registered_adapter(item_completion_policy,
                                     provided=ICompletableItemCompletionPolicy):
                notify(UserProgressRemovedEvent(completable, user, completion_context))

        # Still have a completed item
        assert_that(completed_container, has_length(1))

        events = eventtesting.getEvents(event_type=IObjectRemovedEvent,
                                        filter=lambda x: x.object is completed_item)
        assert_that(events, has_length(1))

        events = eventtesting.getEvents(event_type=IObjectAddedEvent,
                                        filter=lambda x: x.object is completed_item)
        assert_that(events, has_length(1))

        # Verify progress updated even not fired
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(0))

    def _require_completable_for_context(self, completable, completion_context):
        completable_container = ICompletableItemContainer(completion_context)
        completable_container.add_required_item(completable)
        assert_that(completable_container.get_required_keys(), has_length(1))

    def make_context(self):
        ds_folder = component.getUtility(IDataserver).dataserver_folder
        completion_context = MockCompletionContext()
        IConnection(ds_folder).add(completion_context)
        return completion_context


@contextmanager
def _registered_adapter(adapter, **kwargs):
    gsm = component.getGlobalSiteManager()
    gsm.registerAdapter(adapter, **kwargs)
    try:
        yield
    finally:
        gsm.unregisterAdapter(adapter, **kwargs)
