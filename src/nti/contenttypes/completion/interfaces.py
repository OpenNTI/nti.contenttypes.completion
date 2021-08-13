#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class,expression-not-assigned

from zope import component
from zope import interface

from zope.annotation.interfaces import IAttributeAnnotatable

from zope.container.constraints import contains
from zope.container.constraints import containers

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from zope.interface.interfaces import ObjectEvent
from zope.interface.interfaces import IObjectEvent

from zope.security.interfaces import IPrincipal

from nti.base.interfaces import ILastModified

from nti.ntiids.schema import ValidNTIID

from nti.property.property import alias

from nti.schema.field import Bool
from nti.schema.field import Float
from nti.schema.field import Object
from nti.schema.field import Number
from nti.schema.field import Choice
from nti.schema.field import TextLine
from nti.schema.field import ValidDatetime
from nti.schema.field import ValidTextLine
from nti.schema.field import UniqueIterable

from nti.zope_catalog.interfaces import INoAutoIndexEver


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
    Principal.setTaggedValue('_ext_excluded_out', True)

    Item = Object(ICompletableItem,
                  title=u'The completable item',
                  required=True)
    Item.setTaggedValue('_ext_excluded_out', True)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"""The date on which the item
                                  was completed by the user""",
                                  required=True)

    Success = Bool(title=u"Successfully completed",
                   description=u"Indicates the user has successfully completed this item.",
                   default=True)

    ItemNTIID = ValidNTIID(title=u"Completed Item NTIID", required=False, default=None)


class ICompletionContext(ICompletableItem, IAttributeAnnotatable):
    """
    A :class:`ICompletableItem` that may be completed by completing one or many
    :class:`ICompletableItem` objects (defined by a
    :class:`ICompletionContextCompletionPolicy`).
    """

class ICompletionSubContext(interface.Interface):
    """
    A marker interface that indicates this object's
    :class:`ICompletionContext` is in some ways subordinate to some
    higher :class:`IComplectionContext`. An :class:`ICompletionSubContext`'s
    :class:`ICompletionContext` may have the application
    of portions of its :class:`ICompletionContextCompletionPolicy`
    inherited or restricted by the :class:`IComplectionContext` we are
    subordinate to.

    See also:
    https://github.com/NextThought/nti.contenttypes.completion/pull/55
    """
    interface.taggedValue('_ext_is_marker_interface', True)


class ICompletionContextCompletedItem(ICompletedItem):
    """
    A :class:`ICompletedItem` for a :class:`ICompletionContext`.
    """


class ICompletionContextProvider(interface.Interface):
    """
    Something that can provide a :class: `ICompletionContext` for a specific :class: `ICompletableItem`.
    """
    def __call__(completableItem):
        """
        A callable that returns an ICompletionContext object.
        """


class ICompletableItemProvider(interface.Interface):
    """
    An intended subscriber provider of possible :class:`ICompletableItem` objects
    for a :class:`ICompletionContext`.
    """

    def iter_items(user):
        """
        A generator of :class:`ICompletableItem` objects based on the given user.
        """


class IRequiredCompletableItemProvider(interface.Interface):
    """
    An intended subscriber provider of required :class:`ICompletableItem` objects
    for a :class:`ICompletionContext`.
    """

    def iter_items(user):
        """
        A generator of :class:`ICompletableItem` objects based on the given user.
        """

class ICompletedItemProvider(ILastModified):
    """
    An object that can provide :class:`ICompletedItem` objects.  Typically
    registered as a subscriber on :class:`IUser` and :class:`ICompletionContext`
    """

    def completed_items():
        """
        A generator of :class:`ICompletedItem` objects.
        """


class ICertificateRenderer(interface.Interface):

    macro_name = ValidTextLine(title=u'The cert macro name',
                               required=True,
                               default=u'certificate')


class ICompletableItemCompletionPolicy(IContained):
    """
    A policy for :class:`ICompletableItem` objects that determines the
    conditions in which the :class:`ICompletableItem' object can be
    considered complete.
    """

    offers_completion_certificate = Bool(title=u'Offers Completion Certificate',
                                         description=u"""Whether a certificate is offered
                                         for the completion of the completion-context.""",
                                         required=True,
                                         default=False)
    
    certificate_renderer_name = ValidTextLine(title=u"The certificate name",
                                              description=u"""The certificate name in use""",
                                              required=False,
                                              default=None)
    
    certificate_renderer_name = Choice(vocabulary='nti.contenttypes.completion.certificate_vocabulary',
                                       title=u'The certificate renderer',
                                       required=False,
                                       default=None)

    def is_complete(progress):
        """
        Determines if the given :class:`IProgress` is enough for the item to be
        considered complete. If complete, will return a :class:`ICompletedItem`.
        """


class ICompletableItemAggregateCompletionPolicy(ICompletableItemCompletionPolicy):
    """
    A :class:`ICompletableItemCompletionPolicy` that bases completion based
    on what fraction of progress has been made.
    """

    percentage = Number(title=u"Percentage",
                        description=u"""The percentage of progress that must
                        be made for this context to be considered complete.""",
                        required=True,
                        min=0.0,
                        max=1.0,
                        default=1.0)


class ICompletionContextCompletionPolicy(interface.Interface):
    """
    A marker interface for the :class:`ICompletableItemCompletionPolicy` for
    :class:`ICompletionContext` objects that determines the conditions in which the
    :class:`ICompletionContext' object can be considered complete.
    """
# pylint: disable=no-value-for-parameter
ICompletionContextCompletionPolicy.setTaggedValue('_ext_is_marker_interface', True)


class ICompletionContextCompletionPolicyFactory(interface.Interface):
    """
    A callable that can be registered to generate a
    :class:`ICompletionContextCompletionPolicy` for on demand for a
    :class:`ICompletionContext`.
    """


class ICompletionContextCompletionPolicyContainer(IContainer):
    """
    For a :class:`ICompletionContext`, stores the context's
    :class:`ICompletableItemCompletionPolicy` as well as a mapping of
    this context's :class:`ICompletableItem` completion policies.
    """

    context_policy = Object(ICompletableItemCompletionPolicy,
                            title=u"The context's completion policy",
                            description=u"The principal who completed the item",
                            required=False)

    context_policy.setTaggedValue('_ext_excluded_out', True)

    def set_context_policy(context_policy, do_notify=True):
        """
        Update the context_policy, and fire :class:`ICompletionContextCompletionPolicyUpdated` if do_notify is True.
        """


class ICompletionContextCompletionPolicyConfigurationUtility(interface.Interface):

    def can_edit_completion_policy(completion_context):
        """
        Determining if completion policy for a :class: `ICompletionContext` is open to be edited,
        currently we use this to determine if an edit link should decorated on the completion policy object.
        """


class ICompletionContextCompletionPolicyUpdated(interface.Interface):
    """
    When a :class:`ICompletionContextCompletionPolicy` is added or reset for a :class:`ICompletionContext`,
    it would fire this event. currently use this to override section's CompletionPolicy when parent's changed.
    """
    completion_context = Object(ICompletionContext,
                                title=u'The completion context',
                                description=u'The context whose completion policy is updated',
                                required=True)


@interface.implementer(ICompletionContextCompletionPolicyUpdated)
class CompletionContextCompletionPolicyUpdated(object):

    def __init__(self, completion_context):
        self.completion_context = completion_context


class ICompletableItemDefaultRequiredPolicy(interface.Interface):
    """
    A policy for :class:`ICompletionContext` objects that defines
    objects that, by default, are required for completion.
    """

    creator = interface.Attribute(u"The creator of this object.")

    mime_types = UniqueIterable(value_type=TextLine(title=u'the mimetypes'),
                                title=u"mime types of required objects",
                                description=u"""The mime types of objects that should be
                                             required, by default, for the completion context.""")

    mime_types.setTaggedValue('_ext_excluded_out', True)

    def add_mime_types(mime_types):
        """
        Add the given mimetypes into this policy.
        """

    def set_mime_types(mime_types):
        """
        Set mime_types with new mime_types
        """


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

    def clear():
        """
        Clear this container
        """


class IPrincipalCompletedItemContainer(IContainer, IContained, INoAutoIndexEver):
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

    # We persistently store the completion context completed item here.
    # Currently, we *only* use this to broadcast context completed state the
    # *first* this occurs. We do not use then to indicate current context
    # completion state. To do so correctly, we need more questions answered
    # wrt changing requirement states.
    ContextCompletedItem = Object(ICompletionContextCompletedItem,
                                  title=u'The completion context completed item',
                                  required=False)

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

    def remove_principal(principal):
        """
        Remove all :class:`ICompletableItem` objects for the given
        principal.
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
                              default=None,
                              required=False)

    MaxPossibleProgress = Number(title=u"A number indicating the max possible progress that could be made on an item. May be null.",
                                 default=None,
                                 required=False)

    PercentageProgress = Float(title=u"A percentage measure of how much progress exists",
                               required=True,
                               readonly=True,
                               min=0.0,
                               max=1.0)

    HasProgress = Bool(title=u"Indicates the user has some progress on this item.",
                       default=False)

    NTIID = ValidTextLine(title=u"The ntiid of the :class:`ICompletableItem.",
                          required=True)

    Item = Object(ICompletableItem, title=u"Completable item", required=True)
    Item.setTaggedValue('_ext_excluded_out', True)

    User = Object(IPrincipal, title=u"principal", required=True)
    User.setTaggedValue('_ext_excluded_out', True)

    CompletionContext = Object(ICompletionContext,
                               title=u"Completion context",
                               required=True)
    CompletionContext.setTaggedValue('_ext_excluded_out', True)

    LastModified = ValidDatetime(title=u"The date of the last progress.",
                                 required=False)


class ICompletionContextProgress(IProgress):
    """
    A transient object that indicates the progress made on an
    :class:`ICompletionContext` object. This object will also describe if/when
    the context was considered complete
    """

    CompletedItem = Object(ICompletedItem,
                           title=u"The completed item for this context, if applicable",
                           required=False)

    UnsuccessfulItemNTIIDs = UniqueIterable(value_type=ValidNTIID(title=u'the ntiid'),
                                            title=u"Failed item ntiids",
                                            description=u"""NTIIDs of objects the user completed, but
                                                          not successfully.""")

    IncompleteItemNTIIDs = UniqueIterable(value_type=ValidNTIID(title=u'the ntiid'),
                                            title=u"Incomplete item ntiids",
                                            description=u"""NTIIDs of objects the user has not yet completed.""")

    Completed = Bool(title=u"Indicates the user has completed this item.",
                     default=False)

    CompletedDate = ValidDatetime(title=u"The completed date",
                                  description=u"The date on which the item was completed by the user",
                                  default=None,
                                  required=False)


class IUserProgressEvent(IObjectEvent):

    user = Object(IPrincipal, title=u"principal", required=True)

    item = Object(ICompletableItem,
                  title=u"Completable item",
                  required=True)

    context = Object(ICompletionContext,
                     title=u"Completion context",
                     required=True)


class IUserProgressUpdatedEvent(IUserProgressEvent):
    """
    Event to indicate a user has made progress on a :class:`ICompletableItem`,
    within a :class:`ICompletionContext`.
    """


class IUserProgressRemovedEvent(IUserProgressEvent):
    """
    Event to indicate a user's progress on a :class:`ICompletableItem`
    within a :class:`ICompletionContext` may have been reset/removed from
    the system.
    """


class AbstractUserProgressEvent(ObjectEvent):

    item = alias('object')

    def __init__(self, obj, user, context):
        super(AbstractUserProgressEvent, self).__init__(obj)
        self.user = user
        self.context = context


@interface.implementer(IUserProgressUpdatedEvent)
class UserProgressUpdatedEvent(AbstractUserProgressEvent):
    pass


@interface.implementer(IUserProgressRemovedEvent)
class UserProgressRemovedEvent(AbstractUserProgressEvent):
    pass


class ICompletionContextCompletedEvent(IObjectEvent):
    """
    An event indicating this user has successfully completed
    the :class:`ICompletionContext`.
    """
    user = Object(IPrincipal, title=u"principal", required=True)

    context = Object(ICompletionContext,
                     title=u"Completion context",
                     required=True)


@interface.implementer(ICompletionContextCompletedEvent)
class CompletionContextCompletedEvent(ObjectEvent):

    context = alias('object')

    def __init__(self, context, user):
        super(CompletionContextCompletedEvent, self).__init__(context)
        self.user = user

# catalog


class ISiteAdapter(interface.Interface):
    """
    Adapts contained objects to their site.
    """
    site = interface.Attribute("site string")


class IPrincipalAdapter(interface.Interface):
    """
    Adapts contained objects to their principal id.
    """
    id = interface.Attribute("principal id string")


class ICompletionTimeAdapter(interface.Interface):
    """
    Adapts contained objects to their completion time.
    """
    completionTime = interface.Attribute("completion timestamp")


class IItemNTIIDAdapter(interface.Interface):
    """
    Adapts contained objects to their item NTIID.
    """
    ntiid = interface.Attribute("NTIID string")


class ISuccessAdapter(interface.Interface):
    """
    Adapts contained objects to their completion success.
    """
    success = interface.Attribute("success bool")


class IContextNTIIDAdapter(interface.Interface):
    """
    Adapts contained objects to their context NTIID.
    """
    ntiid = interface.Attribute("NTIID string")


class ICompletables(interface.Interface):
    """
    A predicate to return completable objects

    These will typically be registered as named utilities
    """

    def iter_objects():
        """
        return an iterable of :class:`.ICompletableItem` objects
        """


def get_completables():
    predicates = component.getUtilitiesFor(ICompletables)
    for _, predicate in list(predicates):
        for obj in predicate.iter_objects():
            yield obj
