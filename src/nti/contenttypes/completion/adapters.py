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

from nti.contenttypes.completion.interfaces import ICompletionContext
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
    Stores mappings of username -> IIUserCompletedItemContainer for a user.
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
