#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest
from datetime import datetime

import fudge

import BTrees

from zope import component

from nti.zope_catalog.interfaces import IDeferredCatalog

from nti.contenttypes.completion.completion import CompletedItem

from nti.contenttypes.completion.index import IX_SUCCESS
from nti.contenttypes.completion.index import IX_PRINCIPAL
from nti.contenttypes.completion.index import IX_ITEM_NTIID
from nti.contenttypes.completion.index import IX_COMPLETIONTIME

from nti.contenttypes.completion.index import COMPLETED_ITEM_CATALOG_NAME

from nti.contenttypes.completion.index import create_completed_item_catalog
from nti.contenttypes.completion.index import install_completed_item_catalog

from nti.contenttypes.completion.index import CompletedItemCatalog

from nti.contenttypes.completion.tests.test_models import MockUser
from nti.contenttypes.completion.tests.test_models import MockCompletableItem

from nti.contenttypes.completion.tests import SharedConfiguringTestLayer


class TestIndex(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def test_catalog(self):
        now = datetime.utcnow()
        user1 = MockUser(u'user1')
        completable1 = MockCompletableItem('completable1')
        completed = CompletedItem(Principal=user1,
                                  Item=completable1,
                                  CompletedDate=now,
                                  Success=False)
        # test catalog
        catalog = create_completed_item_catalog(family=BTrees.family64)
        assert_that(isinstance(catalog, CompletedItemCatalog),
                    is_(True))
        assert_that(catalog, has_length(6))
        # test index
        catalog.force_index_doc(1, completed)
        for name in (IX_SUCCESS, IX_PRINCIPAL, IX_COMPLETIONTIME, IX_ITEM_NTIID):
            index = catalog[name]
            index = getattr(index, 'index', index)
            assert_that(index,
                        has_property('documents_to_values', has_length(1)))

    def test_install_completed_item_catalog(self):
        intids = fudge.Fake().provides('register').has_attr(family=BTrees.family64)
        catalog = install_completed_item_catalog(component, intids)
        assert_that(catalog, is_not(none()))
        component.getGlobalSiteManager().unregisterUtility(catalog, IDeferredCatalog,
                                                           COMPLETED_ITEM_CATALOG_NAME)
