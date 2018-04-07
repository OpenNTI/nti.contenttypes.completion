#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import BTrees

from zope import component
from zope import interface

from zope.intid.interfaces import IIntIds

from zope.location import locate

from nti.contenttypes.completion.interfaces import ISiteAdapter
from nti.contenttypes.completion.interfaces import ISuccessAdapter
from nti.contenttypes.completion.interfaces import IPrincipalAdapter
from nti.contenttypes.completion.interfaces import IItemNTIIDAdapter
from nti.contenttypes.completion.interfaces import IContextNTIIDAdapter
from nti.contenttypes.completion.interfaces import ICompletionTimeAdapter

from nti.zope_catalog.catalog import DeferredCatalog

from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from nti.zope_catalog.index import AttributeValueIndex
from nti.zope_catalog.index import NormalizationWrapper
from nti.zope_catalog.index import IntegerValueIndex as RawIntegerValueIndex

from nti.zope_catalog.interfaces import IDeferredCatalog

COMPLETED_ITEM_CATALOG_NAME = 'nti.dataserver.++etc++completed-item-catalog'

#: Site
IX_SITE = 'site'

#: Success
IX_SUCCESS = 'success'

#: Completable ntiid
IX_ITEM_NTIID = 'itemNTIID'

#: Context ntiid
IX_CONTEXT_NTIID = 'contextNTIID'

#: Completion time
IX_COMPLETIONTIME = 'completionTime'

#: Principal
IX_USERNAME = IX_PRINCIPAL = 'principal'

logger = __import__('logging').getLogger(__name__)


class SiteIndex(AttributeValueIndex):
    default_field_name = 'site'
    default_interface = ISiteAdapter


class PrincipalIndex(AttributeValueIndex):
    default_field_name = 'id'
    default_interface = IPrincipalAdapter


class ItemNTIIDIndex(AttributeValueIndex):
    default_field_name = 'ntiid'
    default_interface = IItemNTIIDAdapter


class ContextNTIIDIndex(AttributeValueIndex):
    default_field_name = 'ntiid'
    default_interface = IContextNTIIDAdapter


class SucessIndex(AttributeValueIndex):
    default_field_name = 'success'
    default_interface = ISuccessAdapter


class CompletionTimeRawIndex(RawIntegerValueIndex):
    pass


def CompletionTimeIndex(family=BTrees.family64):
    return NormalizationWrapper(field_name='completionTime',
                                interface=ICompletionTimeAdapter,
                                index=CompletionTimeRawIndex(family=family),
                                normalizer=TimestampToNormalized64BitIntNormalizer())


@interface.implementer(IDeferredCatalog)
class CompletedItemCatalog(DeferredCatalog):

    def force_index_doc(self, doc_id, obj):  # BWC
        return super(CompletedItemCatalog, self).index_doc(doc_id, obj)


def create_completed_item_catalog(catalog=None, family=BTrees.family64):
    if catalog is None:
        catalog = CompletedItemCatalog(family=family)
    for name, clazz in ((IX_SITE, SiteIndex),
                        (IX_SUCCESS, SucessIndex),
                        (IX_PRINCIPAL, PrincipalIndex),
                        (IX_ITEM_NTIID, ItemNTIIDIndex),
                        (IX_CONTEXT_NTIID, ContextNTIIDIndex),
                        (IX_COMPLETIONTIME, CompletionTimeIndex),):
        index = clazz(family=family)
        locate(index, catalog, name)
        catalog[name] = index
    return catalog


def get_completed_item_catalog(registry=component):
    return registry.queryUtility(IDeferredCatalog, name=COMPLETED_ITEM_CATALOG_NAME)


def install_completed_item_catalog(site_manager_container, intids=None):
    lsm = site_manager_container.getSiteManager()
    intids = lsm.getUtility(IIntIds) if intids is None else intids
    catalog = get_completed_item_catalog(registry=lsm)
    if catalog is not None:
        return catalog

    catalog = create_completed_item_catalog(family=intids.family)
    locate(catalog, site_manager_container, COMPLETED_ITEM_CATALOG_NAME)
    intids.register(catalog)
    lsm.registerUtility(catalog,
                        provided=IDeferredCatalog,
                        name=COMPLETED_ITEM_CATALOG_NAME)

    for index in catalog.values():
        intids.register(index)
    return catalog
