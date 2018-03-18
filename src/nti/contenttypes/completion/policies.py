#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.container.contained import Contained

from nti.contenttypes.completion.interfaces import ICompletableItemAggregateCompletionPolicy

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICompletableItemAggregateCompletionPolicy)
class CompletableItemAggregateCompletionPolicy(PersistentCreatedAndModifiedTimeObject,
                                               SchemaConfigured,
                                               Contained):

    createDirectFieldProperties(ICompletableItemAggregateCompletionPolicy)

    mimeType = mime_type = "application/vnd.nextthought.completion.aggregatecompletionpolicy"

    def is_complete(self, progress):
        """
        Determines if the given :class:`IProgress` is enough for the item to be
        considered complete.
        """
        # If nothing set, we return True
        result = True
        if self.percentage:
            if progress.MaxPossibleProgress:
                ratio = progress.AbsoluteProgress / progress.MaxPossibleProgress
                result = ratio >= self.percentage
            else:
                # This case should be avoided...
                # Required percentage but not given a denominator
                logger.warning('No MaxPossibleProgress given when computing completion (%s/%s)',
                               progress.AbsoluteProgress,
                               progress.MaxPossibleProgress)
                result = False
        return result

