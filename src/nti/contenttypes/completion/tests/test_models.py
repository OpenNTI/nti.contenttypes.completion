#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import equal_to
from hamcrest import assert_that

import unittest

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from nti.contenttypes.completion.interfaces import ICompletionContext

from nti.contenttypes.completion.tests.interfaces import ITestPrincipal
from nti.contenttypes.completion.tests.interfaces import ITestCompletableItem

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.wref.interfaces import IWeakRef


@interface.implementer(ITestPrincipal)
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


@interface.implementer(ITestCompletableItem)
class MockCompletableItem(PersistentCreatedAndModifiedTimeObject):

    def __init__(self, ntiid):
        self.ntiid = ntiid

    def __conform__(self, iface):
        if iface == IWeakRef:
            return _IdentityWref(self)


@interface.implementer(ICompletionContext, IAttributeAnnotatable)
class MockCompletionContext(PersistentCreatedAndModifiedTimeObject):
    pass


class TestModels(unittest.TestCase):

    def test_wref(self):
        ref_1 = _IdentityWref(None)
        ref_2 = _IdentityWref(object())
        assert_that(ref_1, equal_to(ref_2))
        assert_that(hash(ref_1), is_(42))
