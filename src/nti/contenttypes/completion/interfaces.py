#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.container.constraints import contains
from zope.container.constraints import containers

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from nti.coremetadata.interfaces import IUser

from nti.property.property import alias

from nti.schema.field import Set
from nti.schema.field import Bool
from nti.schema.field import Dict
from nti.schema.field import Text
from nti.schema.field import Choice
from nti.schema.field import Object
from nti.schema.field import Number
from nti.schema.field import Iterable
from nti.schema.field import Timedelta
from nti.schema.field import ValidText
from nti.schema.field import ListOrTuple
from nti.schema.field import ValidDatetime
from nti.schema.field import ValidTextLine
from nti.schema.field import UniqueIterable
from nti.schema.field import TupleFromObject

from nti.schema.jsonschema import TAG_UI_TYPE
from nti.schema.jsonschema import UI_TYPE_EMAIL
from nti.schema.jsonschema import TAG_HIDDEN_IN_UI
from nti.schema.jsonschema import TAG_REQUIRED_IN_UI


class ICompletableItem(interface.Interface):
    """
    A interface for items that may be completable once certain conditions are
    met.
    """


class ICompletedItem(IContained):
    """
    Metadata information about the user, item, time when an
    :class:`ICompletableItem` was completed.
    """

    User = Object(IUser,
                  title=u'The user',
                  description=u"The user who completed the item",
                  required=True)

    Item = Object(ICompletableItem,
                  title=u'The completable item',
                  required=True)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"The date on which the item was completed by the user",
                                  required=True)


class ICompletionContext(ICompletableItem):
    """
    A :class:`ICompletableItem` that may be completed by completing one or many
    :class:`ICompletableItem` objects (defined by a
    :class:`ICompletionContextCompletionPolicy`).
    """

    def has_user_completed_item(user, item):
        """
        Returns a :class:`ICompletedItem` if the given user has completed the
        given item.
        """


class ICompletableItemCompletionPolicy(interface.Interface):
    """
    A policy for :class:`ICompletableItem` objects that determines the
    conditions in which the :class:`ICompletableItem' object can be
    considered complete.
    """

    def is_complete(progress):
        """
        Determines if the given progress is enough for the item to be
        considered complete.
        """


class ICompletionContextCompletionPolicy(ICompletableItemCompletionPolicy):
    """
    A :class:`ICompletableItemCompletionPolicy` for :class:`ICompletionContext` objects
    that determines the conditions in which the :class:`ICompletionContext'
    object can be considered complete, usually as a function of how many
    underlying :class:`ICompletableItem` items have been completed.
    """

    Count = Number(title=u"The number of items",
                   description=u"""The number of items, that once complete by
                   a user will enable the overarching context to be considered
                   complete""",
                   required=False,
                   min=0.0,
                   default=None)

    Percentage = Number(title=u"Percentage of required items",
                        description=u"""The percentage of required items, that
                        once complete by a user will enable the overarching
                        context to be considered complete""",
                        required=False,
                        min=0.0,
                        max=1.0,
                        default=None)


class ICompletableItemDefaultRequiredPolicy(interface.Interface):
    """
    A policy for :class:`ICompletionContext` objects that defines
    objects that, by default, are required for completion.
    """

    mime_types = Set(title=u"mime types of required objects",
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

    def add_optional_item(item):
        """
        Add a :class:`ICompletableItem` to this context as not required.
        """


class IUserCompletedItemContainer(IContainer, IContained):
    """
    Contains :class:`ICompletedItem` that have been completed by a user in a
    :class:`ICompletionContext`.
    """

    contains(ICompletedItem)
    containers('.ICompletedItemContainer')

    User = Object(IUser,
                  title=u'The user',
                  description=u"The user who has completed these items.",
                  required=True)

    def add_completed_item(item):
        """
        Add a :class:`ICompletedItem` to the container.
        """

    def get_completed_item(item):
        """
        Return the :class:`ICompletedItem` from this container, returning
        None if it does not exist.
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
    :class:`IUserCompletedItemContainer` objects.
    """

    contains(IUserCompletedItemContainer)

    def remove_item(item):
        """
        Remove all :class:`ICompletedItem` referenced by the given
        :class:`ICompletableItem`.
        """


class IProgress(interface.Interface):
    """
    Indicates the progress made on underlying :class:`ICompletableItem`
    content, generally only useful to inform on progress towards
    completing an item that is not yet completed.
    """

    AbsoluteProgress = Number(title=u"A number indicating the absolute progress made on an item.",
                              default=0)

    MaxPossibleProgress = Number(title=u"A number indicating the max possible progress that could be made on an item. May be null.",
                                 default=0)

    HasProgress = Bool(title=u"Indicates the user has some progress on this item.",
                       default=False)

    ntiid = ValidTextLine(title=u"The ntiid of the :class:`ICompletableItem.",
                          required=True)

    LastModified = ValidDatetime(title=u"The date of the last progress.",
                                 required=False)


class IUserProgressUpdatedEvent(IObjectEvent):
    """
    Event to indicate a user has made progress on a :class:`ICompletableItem`,
    within a :class:`ICompletionContext`.
    """

    user = Object(IUser, title=u"User", required=True)

    item = Object(ICompletableItem,
                  title=u"Completable item",
                  required=True)

    context = Object(ICompletionContext,
                     title=u"Completion context",
                     required=True)


class UserProgressUpdatedEvent(ObjectEvent):

    item = alias('object')

    def __init__(self, obj, user, context):
        super(UserProgressUpdatedEvent, self).__init__(obj)
        self.user = user
        self.context = context
