#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from unittest import TestCase

import fudge

from hamcrest import contains
from hamcrest import assert_that
from hamcrest import has_length
from hamcrest import starts_with

from zope import component
from zope import interface

from zope.component import eventtesting

from zope.lifecycleevent import IObjectRemovedEvent

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import IUserProgressUpdatedEvent

from nti.contenttypes.completion.tests import DSSharedConfiguringTestLayer

from nti.contenttypes.completion.tests.test_models import MockCompletableItem

from nti.contenttypes.completion.utils import remove_completion

from nti.contenttypes.courses.courses import CourseAdministrativeLevel
from nti.contenttypes.courses.courses import CourseInstance

from nti.coremetadata.interfaces import IDataserver

from nti.dataserver.tests.mock_dataserver import WithMockDSTrans

from nti.dataserver.users import User


class TestRemoveCompletion(TestCase):

    layer = DSSharedConfiguringTestLayer

    @fudge.patch('nti.contenttypes.completion.utils.logger')
    def test_no_container(self, logger):
        args = []

        def warning(*args_, **_kwargs):
            args.append(args_)

        logger.provides('warning').calls(warning)

        context = object()
        remove_completion(None, "test_ntiid", None, context)

        assert_that(args, has_length(1))
        assert_that(args[0], contains(starts_with("No container found"),
                                      "test_ntiid",
                                      context))

    @WithMockDSTrans
    def test_no_completed_item(self):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))

        self._test_remove_completion(obj, prin, None)

        # Verify only removal event fired
        events = eventtesting.getEvents(event_type=IObjectRemovedEvent)
        assert_that(events, has_length(0))
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(0))

    @WithMockDSTrans
    def test_not_successful_completion(self):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin, success=False)

        self._test_remove_completion(obj, prin, completed_item)

        # Verify only removal event fired
        events = eventtesting.getEvents(event_type=IObjectRemovedEvent,
                                        filter=lambda x: x.object is completed_item)
        assert_that(events, has_length(1))
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(0))

    @WithMockDSTrans
    def test_successful_completion_not_required(self):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin)

        self._test_remove_completion(obj, prin, completed_item)

        # Verify only removal event fired
        events = eventtesting.getEvents(event_type=IObjectRemovedEvent,
                                        filter=lambda x: x.object is completed_item)
        assert_that(events, has_length(1))
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(0))

    @WithMockDSTrans
    def test_successful_completion_required(self):
        obj = MockCompletableItem("test_ntiid")
        prin = IPrincipal(User.create_user(username='completion_tester'))
        completed_item = self._fake_completed_item(obj.ntiid, prin)

        self._test_remove_completion(obj, prin, completed_item, is_required=True)

        # Verify both events fired
        events = eventtesting.getEvents(event_type=IObjectRemovedEvent,
                                        filter=lambda x: x.object is completed_item)
        assert_that(events, has_length(1))
        events = eventtesting.getEvents(event_type=IUserProgressUpdatedEvent)
        assert_that(events, has_length(1))

    @staticmethod
    def _test_remove_completion(obj, principal_user, completed_item, is_required=False):
        # Set up user and course
        eventtesting.clearEvents()
        course = CourseInstance()
        admin = CourseAdministrativeLevel()
        ds_root = component.getUtility(IDataserver).dataserver_folder
        ds_root['admin'] = admin
        admin['course'] = course
        # Provide a completed item in our container that wasn't successful
        principal_container = component.queryMultiAdapter((principal_user, course),
                                                          IPrincipalCompletedItemContainer)

        if completed_item:
            principal_container.add_completed_item(completed_item)

        if is_required:
            ICompletableItemContainer(course).add_required_item(obj)

        # Remove it
        remove_completion(obj, obj.ntiid, principal_user, course)

    @staticmethod
    def _fake_completed_item(item_ntiid, user, success=True):
        completed_item = fudge.Fake('CompletedItem').has_attr(Principal=user,
                                                              Success=success,
                                                              item_ntiid=item_ntiid,
                                                              __parent__=None,
                                                              __name__=None)
        interface.alsoProvides(completed_item, ICompletedItem)
        return completed_item
