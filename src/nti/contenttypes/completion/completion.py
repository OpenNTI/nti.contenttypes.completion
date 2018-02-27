#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.container.contained import Contained

from zope import interface

from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPrincipalCompletedItemContainer)
class PrincipalCompletedItemContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                      SchemaConfigured):
    createDirectFieldProperties(IPrincipalCompletedItemContainer)

    user = alias('Principal')
    __parent__ = None
    __name__ = None

    def __init__(self, principal):
        super(PrincipalCompletedItemContainer, self).__init__()
        self.Principal = principal

    def add_completed_item(self, completed_item):
        """
        Add a :class:`ICompletedItem` to the container.
        """
        assert completed_item.Principal == self.user
        self[completed_item.Item.ntiid] = completed_item

    def get_completed_item(self, item):
        """
        Return the :class:`ICompletedItem` from this container given a
        :class:`ICompletableItem`, returning None if it does not exist.
        """
        return self.get(item.ntiid)

    def get_completed_item_count(self):
        """
        Return the number of completed items by this principal.
        """
        return len(self)

    def remove_item(self, item):
        """
        Remove all :class:`ICompletedItem` referenced by the given
        :class:`ICompletableItem` from this container.
        """
        try:
            del self[item.ntiid]
            result = True
        except KeyError:
            result = False
        return result


@interface.implementer(ICompletedItem)
class CompletedItem(PersistentCreatedAndModifiedTimeObject, Contained, SchemaConfigured):
    createDirectFieldProperties(ICompletedItem)

    __external_can_create__ = False

    __parent__ = None
    __name__ = None
    _item = None

    user = alias('Principal')

    mimeType = mime_type = "application/vnd.nextthought.completion.completeditem"

    # pylint: disable=keyword-arg-before-vararg,super-init-not-called
    def __init__(self, Item=None, *args, **kwargs):
        SchemaConfigured.__init__(self, *args, **kwargs)
        self._item = IWeakRef(Item)

    @property
    def Item(self):
        result = None
        if self._item is not None:
            result = self._item()
        return result
