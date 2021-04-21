#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import contains
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import contains_inanyorder

import unittest

from datetime import datetime
from datetime import timedelta

import BTrees

import fudge

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

from nti.contenttypes.completion.utils import get_indexed_completed_items
from nti.contenttypes.completion.utils import get_indexed_completed_items_intids


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
        assert_that(catalog, has_length(7))

        # test index
        one_day_ago = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        completed2 = CompletedItem(Principal=user1,
                                  Item=completable1,
                                  CompletedDate=one_day_ago,
                                  Success=False)
        completed3 = CompletedItem(Principal=user1,
                                  Item=completable1,
                                  CompletedDate=two_days_ago,
                                  Success=False)

        # test index
        catalog.force_index_doc(1, completed)
        catalog.force_index_doc(2, completed2)
        catalog.force_index_doc(3, completed3)
        for name in (IX_SUCCESS, IX_PRINCIPAL, IX_COMPLETIONTIME, IX_ITEM_NTIID):
            index = catalog[name]
            index = getattr(index, 'index', index)
            assert_that(index,
                        has_property('documents_to_values', has_length(3)))

        # test indexing
        intids = fudge.Fake().provides('queryObject').returns(completed)
        items = get_indexed_completed_items(users='user1',
                                            items='completable1',
                                            sites='unknown',
                                            catalog=catalog,
                                            intids=intids)
        assert_that(items, has_length(0))

        items = get_indexed_completed_items(users=(user1,),
                                            items=(completable1,),
                                            catalog=catalog,
                                            intids=intids)
        assert_that(items, has_length(3))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=0,
                                                max_time=None,
                                                catalog=catalog)
        assert_that(rs, has_length(3))
        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=None,
                                                max_time=100,
                                                catalog=catalog)
        assert_that(rs, has_length(0))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=now,
                                                max_time=None,
                                                catalog=catalog)
        assert_that(rs, contains(1))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=one_day_ago,
                                                max_time=None,
                                                catalog=catalog)
        assert_that(rs, contains_inanyorder(1, 2))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=two_days_ago,
                                                max_time=None,
                                                catalog=catalog)
        assert_that(rs, contains_inanyorder(1, 2, 3))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=two_days_ago,
                                                max_time=one_day_ago,
                                                catalog=catalog)
        assert_that(rs, contains_inanyorder(2, 3))

        rs = get_indexed_completed_items_intids(users=(user1,),
                                                min_time=two_days_ago,
                                                max_time=now,
                                                catalog=catalog)
        assert_that(rs, contains_inanyorder(2, 3, 1))

    def test_install_completed_item_catalog(self):
        intids = fudge.Fake().provides('register').has_attr(family=BTrees.family64)
        catalog = install_completed_item_catalog(component, intids)
        assert_that(catalog, is_not(none()))
        component.getGlobalSiteManager().unregisterUtility(catalog, IDeferredCatalog,
                                                           COMPLETED_ITEM_CATALOG_NAME)
