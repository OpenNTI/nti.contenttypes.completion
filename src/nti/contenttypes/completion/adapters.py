#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from BTrees.OOBTree import OOBTree
from BTrees.OOBTree import OOTreeSet

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from zope.security.interfaces import IPrincipal

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contenttypes.completion.completion import PrincipalCompletedItemContainer

from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ISuccessAdapter
from nti.contenttypes.completion.interfaces import IItemNTIIDAdapter
from nti.contenttypes.completion.interfaces import IPrincipalAdapter
from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import ICompletionTimeAdapter
from nti.contenttypes.completion.interfaces import ICompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef

COMPLETED_ITEM_ANNOTATION_KEY = 'nti.contenttypes.completion.interfaces.ICompletedItemContainer'
COMPLETABLE_ITEM_ANNOTATION_KEY = 'nti.contenttypes.completion.interfaces.ICompletableItemContainer'
COMPLETABLE_ITEM_DEFAULT_REQUIRED_ANNOTATION_KEY = 'nti.contenttypes.completion.interfaces.ICompletableItemDefaultRequiredPolicy'
COMPLETION_CONTAINER_ANNOTATION_KEY = 'nti.contenttypes.completion.interfaces.ICompletionContextCompletionPolicyContainer'

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICompletionContext)
@interface.implementer(ICompletedItemContainer)
class CompletedItemContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                             SchemaConfigured):
    """
    Stores mappings of username -> IPrincipalCompletedItemContainer for a user.
    """
    createDirectFieldProperties(ICompletedItemContainer)

    def get_completed_items(self, item):
        """
        Return all :class:`ICompletedItem` objects for the given
        :class:`ICompletableItem`.
        """
        result = []
        for user_container in self.values():
            completed_item = user_container.get_completed_item(item)
            if completed_item is not None:
                result.append(completed_item)
        return result

    def get_completed_item_count(self, item):
        """
        Return the number of :class:`ICompletedItem` objects for the given
        :class:`ICompletableItem`.
        """
        return len(self.get_completed_items(item))

    def remove_item(self, item):
        """
        Remove all :class:`ICompletedItem` objects referenced by the given
        :class:`ICompletableItem`.
        """
        count = 0
        for user_container in self.values():
            did_remove = user_container.remove_item(item)
            if did_remove:
                count += 1
        return count
    
    def remove_principal(self, user):
        """
        Remove all :class:`ICompletedItem` objects for the specified user
        """
        key = getattr(user, 'username', None) or getattr(user, 'id', user)
        container = self.get(key, None)
        if container is not None:
            container.clear()
            del self[key]
            return True
        return False
    remove_user = remove_principal

    def clear(self):
        for username in list(self.keys()):
            self.remove_principal(username)
        super(CompletedItemContainer, self).clear()

_CompletedItemContainerFactory = an_factory(CompletedItemContainer,
                                            COMPLETED_ITEM_ANNOTATION_KEY)


@component.adapter(ICompletionContext)
@interface.implementer(ICompletableItemContainer)
class CompletableItemContainer(PersistentCreatedAndModifiedTimeObject,
                               SchemaConfigured):
    """
    Stores mappings of item_ntiid -> ICompletableItem.
    """
    createDirectFieldProperties(ICompletableItemContainer)

    def __init__(self):
        super(CompletableItemContainer, self).__init__()
        self._required = OOBTree()
        self._optional = OOBTree()

    def _get_item_key(self, item):
        try:
            key = item.ntiid
        except AttributeError:
            key = item
        return key

    def get_required_keys(self):
        return tuple(self._required.keys())

    def add_required_item(self, item):
        """
        Add a :class:`ICompletableItem` to this context as a required item.
        """
        self.remove_optional_item(item)
        self._required[item.ntiid] = IWeakRef(item)

    def remove_required_item(self, item):
        """
        Remove a :class:`ICompletableItem` as a required item.
        """
        key = self._get_item_key(item)
        try:
            self._required.pop(key)
            result = True
        except KeyError:
            result = False
        return result

    def get_optional_keys(self):
        return tuple(self._optional.keys())

    def add_optional_item(self, item):
        """
        Add a :class:`ICompletableItem` to this context as not required.
        """
        self.remove_required_item(item)
        self._optional[item.ntiid] = IWeakRef(item)

    def remove_optional_item(self, item):
        """
        Remove a :class:`ICompletableItem` as an optional item.
        """
        key = self._get_item_key(item)
        try:
            self._optional.pop(key)
            result = True
        except KeyError:
            result = False
        return result

    def is_item_required(self, item):
        """
        Returns a bool if the given :class:`ICompletableItem` is required.
        """
        key = self._get_item_key(item)
        return key in self._required

    def get_required_item_count(self):
        """
        Return the count of required items.
        """
        return len(self._required)

    def is_item_optional(self, item):
        """
        Returns a bool if the given :class:`ICompletableItem` is optional.
        """
        key = self._get_item_key(item)
        return key in self._optional

    def get_optional_item_count(self):
        """
        Return the count of optional items.
        """
        return len(self._optional)

    def clear(self):
        self._optional.clear()
        self._required.clear()

_CompletableItemContainerFactory = an_factory(CompletableItemContainer,
                                              COMPLETABLE_ITEM_ANNOTATION_KEY)


@component.adapter(ICompletionContext)
@interface.implementer(ICompletionContextCompletionPolicyContainer)
class CompletionContextCompletionPolicyContainer(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                                 SchemaConfigured):
    """
    Stores mappings of ntiid -> ICompletionPolicy for a completable item.
    """
    createDirectFieldProperties(ICompletionContextCompletionPolicyContainer)


_CompletionContextCompletionPolicyContainerFactory = an_factory(CompletionContextCompletionPolicyContainer,
                                                                COMPLETION_CONTAINER_ANNOTATION_KEY)


@component.adapter(ICompletionContext)
@interface.implementer(ICompletableItemDefaultRequiredPolicy)
class CompletableItemDefaultRequiredPolicy(PersistentCreatedAndModifiedTimeObject,
                                           SchemaConfigured):

    createDirectFieldProperties(ICompletableItemDefaultRequiredPolicy)

    mimeType = mime_type = "application/vnd.nextthought.completion.defaultrequiredpolicy"

    creator = None

    def __init__(self, *args, **kwargs):
        super(CompletableItemDefaultRequiredPolicy, self).__init__(*args, **kwargs)
        self.mime_types = OOTreeSet()

    def add_mime_types(self, mime_types):
        self.mime_types.update(mime_types)

    def set_mime_types(self, mime_types):
        self.mime_types = OOTreeSet()
        self.mime_types.update(mime_types)


_CompletableItemDefaultRequiredFactory = an_factory(CompletableItemDefaultRequiredPolicy,
                                                    COMPLETABLE_ITEM_DEFAULT_REQUIRED_ANNOTATION_KEY)


def _create_annotation(obj, factory):
    result = factory(obj)
    if IConnection(result, None) is None:
        try:
            # pylint: disable=too-many-function-args
            IConnection(obj).add(result)
        except (TypeError, AttributeError):  # pragma: no cover
            pass
    return result


def CompletedItemContainerFactory(obj):
    return _create_annotation(obj, _CompletedItemContainerFactory)


def CompletableItemContainerFactory(obj):
    return _create_annotation(obj, _CompletableItemContainerFactory)


def CompletionContextCompletionPolicyContainerFactory(obj):
    return _create_annotation(obj, _CompletionContextCompletionPolicyContainerFactory)


def CompletableItemDefaultRequiredFactory(obj):
    return _create_annotation(obj, _CompletableItemDefaultRequiredFactory)


@component.adapter(IPrincipal, ICompletionContext)
@interface.implementer(IPrincipalCompletedItemContainer)
def _context_to_principal_container(user, completion_context):
    completed_container = ICompletedItemContainer(completion_context)
    principal = IPrincipal(user)
    user_id = principal.id
    try:
        result = completed_container[user_id]
    except KeyError:
        result = PrincipalCompletedItemContainer(principal)
        completed_container[user_id] = result
    return result


@component.adapter(ICompletionContext)
@interface.implementer(ICompletionContextCompletionPolicy)
def _context_to_completion_policy(completion_context):
    container = ICompletionContextCompletionPolicyContainer(completion_context)
    return container.context_policy


# catalog


class _Principal(object):

    __slots__ = ('id',)

    def __init__(self, pid):
        self.id = pid


@component.adapter(ICompletedItem)
@interface.implementer(IPrincipalAdapter)
def _completed_item_to_principal(context):
    principal = IPrincipal(context.Principal, None)
    return _Principal(principal.id) if principal is not None else None


class _CompletionTime(object):

    __slots__ = ('completionTime',)

    def __init__(self, completionTime):
        self.completionTime = completionTime


@component.adapter(ICompletedItem)
@interface.implementer(ICompletionTimeAdapter)
def _completed_item_to_completion_time(context):
    completed = context.CompletedDate
    return _CompletionTime(completed) if completed else None


class _NTIID(object):

    __slots__ = ('ntiid',)

    def __init__(self, ntiid):
        self.ntiid = ntiid


@component.adapter(ICompletedItem)
@interface.implementer(IItemNTIIDAdapter)
def _completed_item_to_item_ntiid(context):
    return _NTIID(context.ItemNTIID)


class _Success(object):

    __slots__ = ('success',)

    def __init__(self, success):
        self.success = success


@component.adapter(ICompletedItem)
@interface.implementer(ISuccessAdapter)
def _completed_item_to_success(context):
    return _Success(context.Success)
