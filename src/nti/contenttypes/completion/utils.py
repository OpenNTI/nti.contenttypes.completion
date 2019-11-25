#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from zope import component

from zope.event import notify

from zope.intid.interfaces import IIntIds

from nti.contenttypes.completion.index import IX_SITE
from nti.contenttypes.completion.index import IX_SUCCESS
from nti.contenttypes.completion.index import IX_PRINCIPAL
from nti.contenttypes.completion.index import IX_ITEM_NTIID
from nti.contenttypes.completion.index import IX_CONTEXT_NTIID

from nti.contenttypes.completion.index import get_completed_item_catalog

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletableItemProvider
from nti.contenttypes.completion.interfaces import UserProgressUpdatedEvent
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import IRequiredCompletableItemProvider
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy

logger = __import__('logging').getLogger(__name__)


def is_item_required(item, context):
    """
    Returns a bool if the given item is `required` in this
    :class:`ICompletionContext`.
    :param item: the :class:`ICompletableItem`
    :param context: the :class:`ICompletionContext`
    """
    if not ICompletableItem.providedBy(item):
        return False
    required_container = ICompletableItemContainer(context)
    default_policy = ICompletableItemDefaultRequiredPolicy(context)
    # pylint: disable=too-many-function-args
    if required_container.is_item_required(item):
        result = True
    elif required_container.is_item_optional(item):
        result = False
    else:
        item_mime_type = getattr(item, 'mime_type', '')
        # pylint: disable=unsupported-membership-test
        result = item_mime_type in default_policy.mime_types
    return result


def update_completion(obj, ntiid, user, context):
    """
    For the given object and user, update the completed state for the
    completion context based on the adapted :class:`IProgress`, if
    necessary.

    :param obj: the :class:`ICompletableItem`
    :param ntiid: the ntiid of the completable item
    :param user: the user who has updated progress on the item
    :param context: the :class:`ICompletionContext`
    """
    principal_container = component.queryMultiAdapter((user, context),
                                                      IPrincipalCompletedItemContainer)
    if principal_container is None:
        # Most likely gave us an empty context, which is an error case.
        logger.warning('No container found for progress update (%s) (%s)',
                       ntiid, context)
        return
    # Update completion if the user has no completion or
    # if they have not completed the item successfully.
    if     ntiid not in principal_container \
        or not principal_container[ntiid].Success:
        policy = component.getMultiAdapter((obj, context),
                                           ICompletableItemCompletionPolicy)
        progress = component.queryMultiAdapter((user, obj, context),
                                               IProgress)
        if progress is not None:
            completed_item = policy.is_complete(progress)
            if completed_item is not None:
                # Pop the old value
                principal_container.remove_item(obj)
                # The completed item we get may be different from the given
                # obj.
                logger.info('Marking item complete (ntiid=%s) (user=%s) (item=%s)',
                            ntiid, user.username, completed_item)
                assert ICompletedItem.providedBy(completed_item), \
                       "Must have completed item"
                principal_container[ntiid] = completed_item
                # We broadcast for the context if we have a successfully completed
                # item where we did not before.
                if      completed_item.Success \
                    and is_item_required(obj, context):
                    notify(UserProgressUpdatedEvent(obj=context,
                                                    user=user,
                                                    context=context))


def get_completed_item(user, context, item):
    """
    Return the :class:`ICompletedItem` for the given context, user and item.
    :param user: the user who has updated progress on the item
    :param context: the :class:`ICompletionContext`
    :param obj: the :class:`ICompletableItem`
    """
    user_container = component.getMultiAdapter((user, context),
                                               IPrincipalCompletedItemContainer)
    return user_container.get_completed_item(item)


def get_completable_items_for_user(user, context):
    """
    Return the possible :class:`ICompletedItem` for the given context and user.
    :param user: the user who has updated progress on the item
    :param context: the :class:`ICompletionContext`
    """
    result = set()
    item_providers = component.subscribers((context,),
                                           ICompletableItemProvider)
    for item_provider in item_providers:
        completable_items = item_provider.iter_items(user)
        result.update(completable_items)
    return result


def get_required_completable_items_for_user(user, context):
    """
    Return the required :class:`ICompletedItem` for the given context and user.
    :param user: the user who has updated progress on the item
    :param context: the :class:`ICompletionContext`
    """
    result = set()
    item_providers = component.subscribers((context,),
                                           IRequiredCompletableItemProvider)
    for item_provider in item_providers:
        completable_items = item_provider.iter_items(user)
        result.update(completable_items)
    return result


def get_indexed_completed_items(users=(), contexts=(), items=(), sites=(),
                                catalog=None, intids=None, success=None):
    """
    Return completed items according to the parameters
    """
    query = {}
    result = []
    catalog = get_completed_item_catalog() if catalog is None else catalog

    # process users/principals
    if users:
        if isinstance(users, six.string_types):
            users = users.split(',')
        users = {
            getattr(x, 'id', None) or getattr(x, 'username', x)
            for x in users
        }
        query[IX_PRINCIPAL] = {'any_of': users}

    # process sites
    if sites:
        if isinstance(sites, six.string_types):
            sites = sites.split(',')
        query[IX_SITE] = {'any_of': sites}

    # process context and items
    for values, index in ((contexts, IX_CONTEXT_NTIID),
                          (items, IX_ITEM_NTIID)):
        if not values:
            continue
        if isinstance(values, six.string_types):
            values = values.split(',')
        values = {getattr(x, 'ntiid', x) for x in values}
        query[index] = {'any_of': values}

    if success is not None:
        query[IX_SUCCESS] = {'any_of': (success,)}

    if query:  # perform query
        intids = component.getUtility(IIntIds) if intids is None else intids
        for doc_id in catalog.apply(query) or ():
            obj = intids.queryObject(doc_id)
            if ICompletedItem.providedBy(obj):
                result.append(obj)
    return result
