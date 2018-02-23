#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.completion.interfaces import IPrincipalCompletedItemContainer

logger = __import__('logging').getLogger(__name__)


@interface.implementer(IPrincipalCompletedItemContainer)
class PrincipalCompletedItemContainer(SchemaConfigured):
    createDirectFieldProperties(IPrincipalCompletedItemContainer)

    user = alias('Principal')

    def __init__(self, principal):
        super(PrincipalCompletedItemContainer, self).__init__()
        self.Principal = principal

    def add_completed_item(self, completed_item):
        """
        Add a :class:`ICompletedItem` to the container.
        """
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
        return self.pop(item.ntiid, None)
