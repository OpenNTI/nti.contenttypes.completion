#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from contextlib import contextmanager

from unittest import TestCase

import fudge

from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import has_properties
from hamcrest import starts_with

from zope import component
from zope import interface

from ZODB.interfaces import IConnection

from zope.component import eventtesting
from zope.lifecycleevent import IObjectAddedEvent

from zope.lifecycleevent import IObjectRemovedEvent

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent

from nti.contenttypes.completion.policies import AbstractCompletableItemCompletionPolicy

from nti.contenttypes.completion.tests import DSSharedConfiguringTestLayer

from nti.contenttypes.completion.tests.interfaces import ITestCompletableItem

from nti.contenttypes.completion.tests.test_models import MockCompletableItem
from nti.contenttypes.completion.tests.test_models import MockCompletionContext

from nti.contenttypes.completion.utils import update_completion

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User


class TestUpdateCompletion(TestCase):

    layer = DSSharedConfiguringTestLayer

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    def test_no_container(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        context = object()
        update_completion(None, "test_ntiid", None, context)

        # Logged missing container
        self._verify_logging_counts(messages, warning=1)
        assert_that(messages['warning'][0][0], starts_with('No container found'))

        # Verify no events fired
        self._verify_events()

    @WithMockDSTrans
    def test_already_successful(self):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin)

        container = self._test_update_completion(obj, prin, completed_item)

        # Completed item preserved
        assert_that(container, has_length(1))

        # Verify no events fired
        self._verify_events()

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_overwrite_successful_to_no_progress(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=None,
                                                 overwrite=True)

        # Completed item removed
        assert_that(container, has_length(0))

        # Logged removal
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Removed progress'))

        # Verify removal and update events fired
        self._verify_events(completed_item,
                            removed=True, progress_updated=True)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_overwrite_successful_to_successful(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item,
                                                 overwrite=True)

        # Completed item replaced
        assert_that(container, has_length(1))

        # Logged completion
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        # Verify no progress update event, since status didn't really change
        self._verify_events(completed_item,
                            removed=True, added=True, progress_updated=False)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_no_progress_to_no_progress(self, _logger):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))

        container = self._test_update_completion(obj, prin, None)

        # No completed item
        assert_that(container, has_length(0))

        # Verify no events fired
        self._verify_events()

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_no_progress_to_successful(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = None
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item)

        # Completed item added
        assert_that(container, has_length(1))

        # Logged addition
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        self._verify_events(completed_item,
                            added=True, progress_updated=True)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_no_progress_to_unsuccessfully_complete(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = None
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=False)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item)

        # Completed item added
        assert_that(container, has_length(1))

        # Logged addition
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        self._verify_events(completed_item,
                            added=True, progress_updated=True)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_no_progress_to_successful_not_required(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = None
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item,
                                                 is_required=False)

        # Completed item added
        assert_that(container, has_length(1))

        # Logged addition
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        self._verify_events(completed_item,
                            added=True, progress_updated=False)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_no_progress_to_unsuccessfully_complete_not_required(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = None
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=False)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item,
                                                 is_required=False)

        # Completed item added
        assert_that(container, has_length(1))

        # Logged addition
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        self._verify_events(completed_item,
                            added=True, progress_updated=False)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_unsuccessfully_complete_to_no_progress(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=False)

        container = self._test_update_completion(obj, prin, completed_item)

        # Container empty
        assert_that(container, has_length(0))

        # Logged removal
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Removed progress'))

        self._verify_events(completed_item, removed=True, progress_updated=True)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_unsuccessfully_complete_to_successful(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=False)
        new_completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=new_completed_item)

        # Completed item replaced
        assert_that(container, has_length(1))
        assert_that(container[obj.ntiid], has_properties(Success=True))

        # Logged replacement
        self._verify_logging_counts(messages, info=1)
        assert_that(messages['info'][0][0], starts_with('Marking item complete'))

        self._verify_events(completed_item,
                            removed=True, added=True, progress_updated=True)

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    @WithMockDSTrans
    def test_overwrite_successful_to_incomplete(self, logger):
        messages = dict(info=[], debug=[], warning=[])
        self._setup_logger(logger, messages)

        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=True)

        container = self._test_update_completion(obj, prin, completed_item,
                                                 progress=object(),
                                                 new_completed_item=None,
                                                 overwrite=True)

        # Completed item removed
        assert_that(container, has_length(0))

        # Logged removal
        self._verify_logging_counts(messages, info=1, debug=1)
        assert_that(messages['info'][0][0], starts_with('Removed progress'))
        assert_that(messages['debug'][0][0], starts_with('Item is not complete'))

        self._verify_events(completed_item,
                            removed=True, progress_updated=True)

    def _verify_logging_counts(self, messages, info=0, debug=0, warning=0):
        assert_that(messages['info'], has_length(info))
        assert_that(messages['debug'], has_length(debug))
        assert_that(messages['warning'], has_length(warning))

    def _test_update_completion(self, obj, principal_user, completed_item,
                                is_required=True,
                                progress=None,
                                new_completed_item=None,
                                overwrite=False):
        # Set up context
        dataserver = component.getUtility(IDataserver)
        ds_folder = dataserver.dataserver_folder
        context = MockCompletionContext()
        IConnection(ds_folder).add(context)

        # Provide the completed item, if necessary
        principal_container = component.queryMultiAdapter((principal_user, context),
                                                          IPrincipalCompletedItemContainer)

        if completed_item is not None:
            principal_container.add_completed_item(completed_item)

        if is_required:
            ICompletableItemContainer(context).add_required_item(obj)

        # Clear events just prior to running
        eventtesting.clearEvents()

        # Setup and register our progress and completion policies
        progress_adapter = fudge.Fake('ProgressAdapter').is_callable().returns(progress)
        item_completion_policy = self._completion_policy(new_completed_item)

        # Update completion
        with _registered_adapter(progress_adapter,
                                 required=(IPrincipal, ITestCompletableItem, ICompletionContext),
                                 provided=IProgress):
            with _registered_adapter(item_completion_policy,
                                     provided=ICompletableItemCompletionPolicy):
                update_completion(obj, obj.ntiid, principal_user, context,
                                  overwrite=overwrite)

        return principal_container

    def _verify_events(self, completed_item=None,
                       removed=False, added=False, progress_updated=False):
        # Verify any additions or removal to/from the completed container
        event_filter = None
        if completed_item is not None:
            def event_filter(event):
                event_object = getattr(event, 'object', None)
                event_ntiid = getattr(event_object, 'item_ntiid', None)
                return event_ntiid == completed_item.item_ntiid

        events = eventtesting.getEvents(event_type=IObjectRemovedEvent,
                                        filter=event_filter)
        assert_that(events, has_length(1 if removed else 0))

        events = eventtesting.getEvents(event_type=IObjectAddedEvent,
                                        filter=event_filter)
        assert_that(events, has_length(1 if added else 0))

        # Verify whether user progress was udpated
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(1 if progress_updated else 0))

    def _completion_policy(self, completed_item):
        # Always returns unsuccessfully completed items
        @component.adapter(ITestCompletableItem, ICompletionContext)
        class MockCompletionPolicy(AbstractCompletableItemCompletionPolicy):

            def __init__(self, *args, **kwargs):
                pass

            def is_complete(self, _progress):
                return completed_item

        return MockCompletionPolicy

    @staticmethod
    def _fake_completed_item(item_ntiid, user, success=True):
        completed_item = fudge.Fake('CompletedItem').has_attr(Principal=user,
                                                              Success=success,
                                                              item_ntiid=item_ntiid,
                                                              __parent__=None,
                                                              __name__=None)
        interface.alsoProvides(completed_item, ICompletedItem)
        return completed_item

    @staticmethod
    def _setup_logger(logger, messages):
        def info(*args, **_kwargs):
            messages['info'].append(args)
        logger.provides('info').calls(info)

        def debug(*args, **_kwargs):
            messages['debug'].append(args)
        logger.provides('debug').calls(debug)

        def warning(*args, **_kwargs):
            messages['warning'].append(args)
        logger.provides('warning').calls(warning)


@contextmanager
def _registered_adapter(adapter, **kwargs):
    gsm = component.getGlobalSiteManager()
    gsm.registerAdapter(adapter, **kwargs)
    try:
        yield
    finally:
        gsm.unregisterAdapter(adapter, **kwargs)
