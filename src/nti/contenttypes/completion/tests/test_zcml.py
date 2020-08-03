#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,no-member

from hamcrest import is_
from hamcrest import not_none
from hamcrest import assert_that
from hamcrest import has_property

from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy

from nti.contenttypes.completion.tests.test_models import MockCompletableItem

import nti.testing.base


ZCML_STRING = """
<configure  xmlns="http://namespaces.zope.org/zope"
            xmlns:i18n="http://namespaces.zope.org/i18n"
            xmlns:zcml="http://namespaces.zope.org/zcml"
            xmlns:completion="http://nextthought.com/ntp/completion">

    <include package="zope.component" file="meta.zcml" />
    <include package="zope.security" file="meta.zcml" />
    <include package="zope.component" />
    <include package="." file="meta.zcml" />

    <configure>
        <completion:registerCompletionPolicy percentage=".5"
                                             for="nti.contenttypes.completion.interfaces.ICompletableItem"/>
    </configure>
</configure>
"""

class TestZcml(nti.testing.base.ConfiguringTestBase):

    def test_policy(self):
        self.configure_string(ZCML_STRING)
        item = MockCompletableItem('ntiid')
        policy = ICompletableItemCompletionPolicy(item)
        assert_that(policy, not_none())
        assert_that(policy,
                    has_property('percentage', is_(.5)))
