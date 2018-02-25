#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import has_length
from hamcrest import assert_that

from nose.tools import assert_raises

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides

import unittest

from zope.schema.interfaces import ValidationError

from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextAggregateCompletionPolicy

from nti.contenttypes.completion.policies import CompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.policies import CompletionContextAggregateCompletionPolicy

from nti.contenttypes.completion.progress import Progress

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer


class TestPolicies(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_context_completion_policy(self):
        completion_policy = CompletionContextAggregateCompletionPolicy()
        assert_that(completion_policy,
                    validly_provides(ICompletionContextAggregateCompletionPolicy))
        assert_that(completion_policy,
                    verifiably_provides(ICompletionContextAggregateCompletionPolicy))
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
