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

from nti.dataserver.interfaces import IUser

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

    Completed = Bool(title=u"Indicates the user has completed this item.",
                     default=False)

    ntiid = ValidTextLine(title=u"The ntiid of the :class:`ICompletableItem.",
                          required=True)

    LastModified = ValidDatetime(title=u"The date of the last progress.",
                                 required=False)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"The date on which the item was completed by the user",
                                  default=None,
                                  required=False)

class ICompletableItem(interface.Interface):
    """
    A interface for items that may be completable under once certain conditions
    are met.
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


class ICompletionContext(interface.Interface):
    """
    An interface identifying an item that may be 'completed', according to a
    user interacting with underlying :class:`ICompletableItem` content in
    such a way to fulfill this context's requirements.
    """

    enabled = Bool(title=u"Completion context enabled",
                   description=u"Whether this completion context has been enabled/disabled",
                   required=True,
                   default=False)


class ICompletableItemContainer(interface.Interface):
    """
    Contains items that are required to be completed for a
    :class:`ICompletionContext` as well as those items explicitly marked
    not-required for our :class:`ICompletionContext`.
    """

    def add_required_item(self, item):
        """
        Add a :class:`ICompletableItem` to this context as a required item.
        """

    def add_optional_item(self, item):
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

    def add_completed_item(self, item):
        """
        Add a :class:`ICompletedItem` to the container.
        """

    def get_completed_item(self, item):
        """
        Return the :class:`ICompletedItem` from this container, returning
        None if it does not exist.
        """


class ICompletedItemContainer(IContainer):
    """
    Contains items that have been completed for the
    :class:`ICompletionContext`, organized with
    :class:`IUserCompletedItemContainer` objects.
    """

    contains(IUserCompletedItemContainer)

