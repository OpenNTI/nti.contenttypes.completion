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

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import IAwardedCompletedItem
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import IPrincipalAwardedCompletedItemContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.dataserver.sharing import AbstractReadableSharedMixin

from nti.dublincore.datastructures import PersistentCreatedModDateTrackingObject

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.fieldproperty import createFieldProperties
from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef
from dns.rdataclass import NONE

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
        self.Principal = IPrincipal(principal)

    def add_completed_item(self, completed_item):
        """
        Add a :class:`ICompletedItem` to the container.
        """
        assert completed_item.Principal == self.user
        self[completed_item.item_ntiid] = completed_item

    def get_completed_item(self, item):
        """
        Return the :class:`ICompletedItem` from this container given a
        :class:`ICompletableItem`, returning None if it does not exist.
        """
        try:
            key = item.ntiid
        except AttributeError:
            key = ''
        return self.get(key)

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
    
@interface.implementer(IPrincipalAwardedCompletedItemContainer)
class PrincipalAwardedCompletedItemContainer(PrincipalCompletedItemContainer):
    
    createDirectFieldProperties(IPrincipalAwardedCompletedItemContainer)
    
    
class CompletedItemMixin(object):
    """
    A mixin for shared functions of CompletedItems and its children objects
    """
    
    @property
    def sharedWith(self):
        return (self.Principal.id,)

    @property
    def Item(self):
        result = None
        if self._item is not None:
            result = self._item()
        return result

    @property
    def ItemNTIID(self):
        return self._item_ntiid or self.__name__


@WithRepr
@interface.implementer(ICompletedItem)
class CompletedItem(PersistentCreatedAndModifiedTimeObject, 
                    Contained,
                    AbstractReadableSharedMixin,
                    CompletedItemMixin):

    __external_can_create__ = False

    __parent__ = None
    __name__ = None
    _item = None
    _item_ntiid = None
    Success = True
    CompletedDate = None

    user = alias('Principal')
    item_ntiid = alias('ItemNTIID')

    mimeType = mime_type = "application/vnd.nextthought.completion.completeditem"

    def __init__(self, Principal=None, Item=None, Success=True, CompletedDate=None, *args, **kwargs):
        # See note in Progress about why this is not schema configured.
        super(CompletedItem, self).__init__(*args, **kwargs)
        self.Success = Success
        self.CompletedDate = CompletedDate
        self._item = IWeakRef(Item)
        self._item_ntiid = Item.ntiid
        self.Principal = IPrincipal(Principal)
    
@WithRepr
@interface.implementer(IAwardedCompletedItem)
class AwardedCompletedItem(PersistentCreatedAndModifiedTimeObject, 
                           Contained,
                           CompletedItemMixin,
                           SchemaConfigured):
    
    createFieldProperties(ICompletedItem)
    createDirectFieldProperties(IAwardedCompletedItem)
    
    __external_can_create__ = True
    
    creator = None
    
    __parent__ = None
    __name__ = None
    _item = None
    _Principal = None
    _awarder = None
    _Item = None
    _item_ntiid = None
    Success = True
    CompletedDate = None

    user = alias('Principal')
    item_ntiid = alias('ItemNTIID')

    mimeType = mime_type = "application/vnd.nextthought.completion.awardedcompleteditem"
    
    def __init__(self, *args, **kwargs):
        SchemaConfigured.__init__(self, *args, **kwargs)
        PersistentCreatedAndModifiedTimeObject.__init__(self)

    @property
    def Principal(self):
        result = None
        if self._Principal is not None:
            result = self._Principal
        return result
        
    @Principal.setter
    def Principal(self, value):
        if value is not None:
            self._Principal = IPrincipal(value)
            
    @property
    def awarder(self):
        result = None
        if self._awarder is not None:
            result = self._awarder
        return result
        
    @awarder.setter
    def awarder(self, value):
        if value is not None:
            self._awarder = IPrincipal(value)
            
    @property
    def Item(self):
        result = None
        if self._Item is not None:
            result = self._Item
        return result
        
    @Item.setter
    def Item(self, value):
        from IPython.terminal.debugger import set_trace;set_trace()
        if value is not None:
            self._Item = IWeakRef(value)
