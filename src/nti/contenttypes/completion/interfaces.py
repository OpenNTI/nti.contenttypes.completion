#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.constraints import contains
from zope.container.constraints import containers

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.security.interfaces import IPrincipal

from nti.property.property import alias

from nti.schema.field import Bool
from nti.schema.field import Object
from nti.schema.field import Number
from nti.schema.field import TextLine
from nti.schema.field import ValidDatetime
from nti.schema.field import ValidTextLine
from nti.schema.field import UniqueIterable


class ICompletableItem(interface.Interface):
    """
    A interface for items that may be completable once certain conditions are
    met.
    """


class ICompletedItem(IContained):
    """
    Metadata information about the principal, item, time when an
    :class:`ICompletableItem` was completed.
    """

    Principal = Object(IPrincipal,
                       title=u'The principal',
                       description=u"The principal who completed the item",
                       required=True)

    Item = Object(ICompletableItem,
                  title=u'The completable item',
                  required=True)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"The date on which the item was completed by the user",
                                  required=True)


class ICompletionContext(ICompletableItem, IAttributeAnnotatable):
    """
    A :class:`ICompletableItem` that may be completed by completing one or many
    :class:`ICompletableItem` objects (defined by a
    :class:`ICompletionContextCompletionPolicy`).
    """


class ICompletableItemCompletionPolicy(interface.Interface):
    """
    A policy for :class:`ICompletableItem` objects that determines the
    conditions in which the :class:`ICompletableItem' object can be
    considered complete.
    """

    def is_complete(progress):
        """
        Determines if the given :class:`IProgress` is enough for the item to be
        considered complete.
        """


class ICompletableItemAggregateCompletionPolicy(ICompletableItemCompletionPolicy):
    """
    A :class:`ICompletableItemCompletionPolicy` that bases completion based
    on how many (or what fraction of) progress has been made.
    """

    count = Number(title=u"The count",
                   description=u"""The absolute progress that must be made to
                   be considered complete.""",
                   required=False,
                   min=0.0,
                   default=None)

    percentage = Number(title=u"Percentage",
                        description=u"""The percentage of progress that must
                        be made for this context to be considered complete.""",
                        required=False,
                        min=0.0,
                        max=1.0,
                        default=None)


class ICompletionContextCompletionPolicy(ICompletableItemCompletionPolicy):
    """
    A :class:`ICompletableItemCompletionPolicy` for :class:`ICompletionContext`
    objects that determines the conditions in which the
    :class:`ICompletionContext' object can be considered complete.
    """


class ICompletableItemDefaultRequiredPolicy(interface.Interface):
    """
    A policy for :class:`ICompletionContext` objects that defines
    objects that, by default, are required for completion.
    """

    mime_types = UniqueIterable(value_type=TextLine(title=u'the mimetype'),
                                title=u"mime types of required objects",
                                description=u"""The mime types of objects that should be
                                             required, by default, for the completion context.""")


class ICompletableItemContainer(interface.Interface):
    """
    Contains items that are required to be completed for a
    :class:`ICompletionContext` as well as those items explicitly marked
    not-required for our :class:`ICompletionContext`.
    """

    def add_required_item(item):
        """
        Add a :class:`ICompletableItem` to this context as a required item.
        """

    def remove_required_item(item):
        """
        Remove a :class:`ICompletableItem` as a required item.
        """

    def is_item_required(item):
        """
        Returns a bool if the given :class:`ICompletableItem` is required.
        """

    def get_required_item_count():
        """
        Return the count of required items.
        """

    def add_optional_item(item):
        """
        Add a :class:`ICompletableItem` to this context as not required.
        """

    def remove_optional_item(item):
        """
        Remove a :class:`ICompletableItem` as an optional item.
        """

    def is_item_optional(item):
        """
        Returns a bool if the given :class:`ICompletableItem` is optional.
        """

    def get_optional_item_count():
        """
        Return the count of optional items.
        """


class IPrincipalCompletedItemContainer(IContainer, IContained):
    """
    Contains :class:`ICompletedItem` that have been completed by a user in a
    :class:`ICompletionContext`.
    """

    contains(ICompletedItem)
    containers('.ICompletedItemContainer')

    Principal = Object(IPrincipal,
                       title=u'The principal',
                       description=u"The user principal has completed these items.",
                       required=True)

    def add_completed_item(completed_item):
        """
        Add a :class:`ICompletedItem` to the container.
        """

    def get_completed_item(item):
        """
        Return the :class:`ICompletedItem` from this container given a
        :class:`ICompletableItem`, returning None if it does not exist.
        """

    def get_completed_item_count():
        """
        Return the number of completed items by this principal.
        """

    def remove_item(item):
        """
        Remove all :class:`ICompletedItem` referenced by the given
        :class:`ICompletableItem` from this container.
        """


class ICompletedItemContainer(IContainer):
    """
    Contains items that have been completed for the
    :class:`ICompletionContext`, organized with
    :class:`IPrincipalCompletedItemContainer` objects.
    """

    contains(IPrincipalCompletedItemContainer)

    def get_completed_items(item):
        """
        Return all :class:`ICompletedItem` objects for the given
        :class:`ICompletableItem`.
        """

    def get_completed_item_count(item):
        """
        Return the number of :class:`ICompletedItem` objects for the given
        :class:`ICompletableItem`.
        """

    def remove_item(item):
        """
        Remove all :class:`ICompletedItem` objects referenced by the given
        :class:`ICompletableItem`, returning the count of removed items.
        """


class IProgress(interface.Interface):
    """
    A transient object that indicates the progress made on an underlying
    :class:`ICompletableItem` content, generally only useful to inform on
    progress towards completing an item that is not yet completed.
    """

    AbsoluteProgress = Number(title=u"A number indicating the absolute progress made on an item.",
                              default=0)

    MaxPossibleProgress = Number(title=u"A number indicating the max possible progress that could be made on an item. May be null.",
                                 default=0)

    HasProgress = Bool(title=u"Indicates the user has some progress on this item.",
                       default=False)

    NTIID = ValidTextLine(title=u"The ntiid of the :class:`ICompletableItem.",
                          required=True)

    LastModified = ValidDatetime(title=u"The date of the last progress.",
                                 required=False)

    Completed = Bool(title=u"Indicates the user has completed this item.",
                     default=False)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"The date on which the item was completed by the user",
                                  default=None,
                                  required=False)


class IUserProgressUpdatedEvent(IObjectEvent):
    """
    Event to indicate a user has made progress on a :class:`ICompletableItem`,
    within a :class:`ICompletionContext`.
    """

    user = Object(IPrincipal, title=u"principal", required=True)

    item = Object(ICompletableItem,
                  title=u"Completable item",
                  required=True)

    context = Object(ICompletionContext,
                     title=u"Completion context",
                     required=True)


@interface.implementer(IUserProgressUpdatedEvent)
class UserProgressUpdatedEvent(ObjectEvent):

    item = alias('object')

    def __init__(self, obj, user, context):
        super(UserProgressUpdatedEvent, self).__init__(obj)
        self.user = user
        self.context = context
