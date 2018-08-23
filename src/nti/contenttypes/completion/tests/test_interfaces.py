#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import has_length
from hamcrest import assert_that

import unittest

from zope import component
from zope import interface

from zope.dottedname import resolve as dottedname


class TestInterfaces(unittest.TestCase):

    def test_import_interfaces(self):
        dottedname.resolve('nti.contenttypes.completion.interfaces')

    def test_get_completables(self):
        
        from nti.contenttypes.completion.interfaces import ICompletables
        from nti.contenttypes.completion.interfaces import get_completables
        
        @interface.implementer(ICompletables)
        class FakeCompletables(object):
        
            def iter_objects(self):
                return (object(),)
    
        completables = FakeCompletables()
        component.getGlobalSiteManager().registerUtility(completables, ICompletables)
        assert_that(list(get_completables()),
                    has_length(1))
        component.getGlobalSiteManager().unregisterUtility(completables, ICompletables)
