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
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer

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
                logger.info('Marking item complete (ntiid=%s) (user=%s)',
                             ntiid, user.username)
                principal_container[ntiid] = completed_item
