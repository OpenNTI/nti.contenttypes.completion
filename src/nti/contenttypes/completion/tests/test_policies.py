#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

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

        completion_policy.count = 10

        completion_policy.count = 0
        completion_policy.percentage = .50

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
