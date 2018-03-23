#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import IUserProgressRemovedEvent
from nti.contenttypes.completion.interfaces import IPrincipalCompletedItemContainer

from nti.contenttypes.completion.utils import update_completion

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICompletableItem, IUserProgressRemovedEvent)
def _progress_removed(item, event):
    principal_container = component.getMultiAdapter((event.user, event.context),
                                                    IPrincipalCompletedItemContainer)
    logger.info('Removing progress for user (%s) (item=%s)',
                event.user, item.ntiid)
    principal_container.remove_item(item)
    update_completion(item, item.ntiid, event.user, event.context)
