#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import contains_inanyorder

from nose.tools import assert_raises

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from zope.schema.interfaces import ValidationError

from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemAggregateCompletionPolicy

from nti.contenttypes.completion.policies import CompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.policies import CompletableItemAggregateCompletionPolicy

from nti.contenttypes.completion.progress import Progress

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer

from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

CLASS = StandardExternalFields.CLASS
ITEMS = StandardExternalFields.ITEMS
MIMETYPE = StandardExternalFields.MIMETYPE


class TestPolicies(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_progress_externalization(self):
        progress = Progress(NTIID=u'ntiid',
                            AbsoluteProgress=10,
                            MaxPossibleProgress=25)
        ext_obj = to_external_object(progress)
        assert_that(ext_obj[CLASS], is_('Progress'))
        assert_that(ext_obj[MIMETYPE], is_('application/vnd.nextthought.completion.progress'))
        assert_that(ext_obj['AbsoluteProgress'], is_(10))
        assert_that(ext_obj['NTIID'], is_(u'ntiid'))
        assert_that(ext_obj['MaxPossibleProgress'], is_(25))
        assert_that(ext_obj['Completed'], is_(False))
        assert_that(ext_obj['CompletedDate'], none())

        factory = find_factory_for(ext_obj)
        assert_that(factory, none())

    def test_policy_externalization(self):
        completion_policy = CompletableItemAggregateCompletionPolicy()
        ext_obj = to_external_object(completion_policy)
        assert_that(ext_obj[CLASS], is_('CompletableItemAggregateCompletionPolicy'))
        assert_that(ext_obj[MIMETYPE], is_('application/vnd.nextthought.completion.aggregatecompletionpolicy'))
        assert_that(ext_obj['count'], none())
        assert_that(ext_obj['percentage'], none())

        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.count, none())
        assert_that(new_io.percentage, none())

        new_io.count = 50
        new_io.percentage = .5
        ext_obj = to_external_object(new_io)
        assert_that(ext_obj['count'], is_(50))
        assert_that(ext_obj['percentage'], is_(.5))

        ext_obj = to_external_object(new_io)
        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.count, is_(50))
        assert_that(new_io.percentage, is_(.5))

    def test_default_policy_externalization(self):
        completable_policy = CompletableItemDefaultRequiredPolicy()
        ext_obj = to_external_object(completable_policy)
        assert_that(ext_obj[CLASS], is_('CompletableItemDefaultRequiredPolicy'))
        assert_that(ext_obj[MIMETYPE], is_('application/vnd.nextthought.completion.defaultrequiredpolicy'))
        assert_that(ext_obj['mime_types'], has_length(0))

        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.mime_types, has_length(0))

        new_io.mime_types.add(u'mime_type1')
        new_io.mime_types.add(u'mime_type2')
        ext_obj = to_external_object(new_io)
        assert_that(ext_obj[CLASS], is_('CompletableItemDefaultRequiredPolicy'))
        assert_that(ext_obj[MIMETYPE], is_('application/vnd.nextthought.completion.defaultrequiredpolicy'))
        assert_that(ext_obj['mime_types'], has_length(2))
        assert_that(ext_obj['mime_types'], contains_inanyorder(u'mime_type1', u'mime_type2'))

        factory = find_factory_for(ext_obj)
        assert_that(factory, not_none())
        new_io = factory()
        update_from_external_object(new_io, ext_obj)
        assert_that(new_io.mime_types, has_length(2))
        assert_that(new_io.mime_types, contains_inanyorder(u'mime_type1', u'mime_type2'))

    def test_context_completion_policy(self):
        completion_policy = CompletableItemAggregateCompletionPolicy()
        assert_that(completion_policy,
                    validly_provides(ICompletableItemAggregateCompletionPolicy))
        assert_that(completion_policy,
                    verifiably_provides(ICompletableItemAggregateCompletionPolicy))
        assert_that(completion_policy.count, none())
        assert_that(completion_policy.percentage, none())

        # No requirements set
        no_progress = Progress(NTIID=u'ntiid')
        some_progress1 = Progress(NTIID=u'ntiid',
                                  AbsoluteProgress=10,
                                  MaxPossibleProgress=25)
        some_progress2 = Progress(NTIID=u'ntiid',
                                  AbsoluteProgress=8,
                                  MaxPossibleProgress=16)
        little_progress = Progress(NTIID=u'ntiid',
                                   AbsoluteProgress=9,
                                   MaxPossibleProgress=20)
        much_progress = Progress(NTIID=u'ntiid',
                                 AbsoluteProgress=20,
                                 MaxPossibleProgress=20)

        assert_that(completion_policy.is_complete(no_progress), is_(True))
        assert_that(completion_policy.is_complete(some_progress1), is_(True))
        assert_that(completion_policy.is_complete(some_progress2), is_(True))
        assert_that(completion_policy.is_complete(little_progress), is_(True))
        assert_that(completion_policy.is_complete(much_progress), is_(True))

        # Count
        completion_policy.count = 10
        assert_that(completion_policy.is_complete(no_progress), is_(False))
        assert_that(completion_policy.is_complete(some_progress1), is_(True))
        assert_that(completion_policy.is_complete(some_progress2), is_(False))
        assert_that(completion_policy.is_complete(little_progress), is_(False))
        assert_that(completion_policy.is_complete(much_progress), is_(True))

        # Percentage
        completion_policy.count = 0
        completion_policy.percentage = .50
        assert_that(completion_policy.is_complete(no_progress), is_(False))
        assert_that(completion_policy.is_complete(some_progress1), is_(False))
        assert_that(completion_policy.is_complete(some_progress2), is_(True))
        assert_that(completion_policy.is_complete(little_progress), is_(False))
        assert_that(completion_policy.is_complete(much_progress), is_(True))

        # Both
        completion_policy.count = 10
        assert_that(completion_policy.is_complete(no_progress), is_(False))
        assert_that(completion_policy.is_complete(some_progress1), is_(False))
        assert_that(completion_policy.is_complete(some_progress2), is_(False))
        assert_that(completion_policy.is_complete(little_progress), is_(False))
        assert_that(completion_policy.is_complete(much_progress), is_(True))

        with assert_raises(ValidationError):
            completion_policy.count = -1
        for new_percentage in (-1, 2, 100):
            with assert_raises(ValidationError):
                completion_policy.percentage = new_percentage

    def test_completable_policy(self):
        completable_policy = CompletableItemDefaultRequiredPolicy()
        assert_that(completable_policy,
                    validly_provides(ICompletableItemDefaultRequiredPolicy))
        assert_that(completable_policy,
                    verifiably_provides(ICompletableItemDefaultRequiredPolicy))
        assert_that(completable_policy.mime_types, has_length(0))

        completable_policy.mime_types.add('mime_type1')
        completable_policy.mime_types.add('mime_type1')
        completable_policy.mime_types.add('mime_type2')
        assert_that(completable_policy.mime_types, has_length(2))
