#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy

logger = __import__('logging').getLogger(__name__)


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
    if ntiid not in principal_container:
        policy = component.getMultiAdapter((obj, context),
                                           ICompletableItemCompletionPolicy)
        progress = component.queryMultiAdapter((user, obj, context),
                                               IProgress)
        if progress is not None:
            completed_item = policy.is_complete(progress)
            if completed_item is not None:
                logger.info('Marking item complete (ntiid=%s) (user=%s) (item=%s)',
                             ntiid, user.username, completed_item)
                assert ICompletedItem.providedBy(completed_item)
                assert completed_item.item_ntiid == ntiid
                principal_container[ntiid] = completed_item


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
    if required_container.is_item_required(item):
        result = True
    elif required_container.is_item_optional(item):
        result = False
    else:
        item_mime_type = getattr(item, 'mime_type', '')
        result = item_mime_type in default_policy.mime_types
    return result


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
