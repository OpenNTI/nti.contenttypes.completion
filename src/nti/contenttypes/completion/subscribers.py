#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletedItemContainer
from nti.contenttypes.completion.interfaces import IUserProgressRemovedEvent
from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyFactory
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.contenttypes.completion.utils import update_completion

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICompletableItem, IUserProgressRemovedEvent)
def _progress_removed(item, event):
    if event.user is not None:
        logger.info('Removing progress for user (%s) (item=%s)',
                event.user, item.ntiid)
        principal_container = component.getMultiAdapter((event.user, event.context),
                                                        IPrincipalCompletedItemContainer)
        principal_container.remove_item(item)
        update_completion(item, item.ntiid, event.user, event.context)


def completion_context_default_policy(completion_context, unused_event=None):
    """
    A subscriber that can be registered (as needed) to add a
    :class:`ICompletionContextCompletionPolicy` to a :class:`ICompletionContext`.
    """
    policy_container = ICompletionContextCompletionPolicyContainer(completion_context)
    if policy_container.context_policy is None:
        policy_factory = component.queryUtility(ICompletionContextCompletionPolicyFactory)
        if policy_factory is not None:
            new_policy = policy_factory()
            if new_policy is not None:
                policy_container.set_context_policy(new_policy)


def completion_context_deleted_event(completion_context, unused_event=None):
    """
    A subscriber that can be registered (as needed) :class:`ICompletionContext` is
    deleted
    """
    for clazz in (ICompletionContextCompletionPolicyContainer,
                  ICompletableItemContainer,
                  ICompletedItemContainer):
        container = clazz(completion_context, None)
        if container:
            # pylint: disable=too-many-function-args
            container.clear()
