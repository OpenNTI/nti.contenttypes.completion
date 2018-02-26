#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from BTrees.OOBTree import OOTreeSet

from zope import interface

from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemAggregateCompletionPolicy

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICompletableItemAggregateCompletionPolicy)
class CompletableItemAggregateCompletionPolicy(PersistentCreatedAndModifiedTimeObject,
                                               SchemaConfigured):

    createDirectFieldProperties(ICompletableItemAggregateCompletionPolicy)

    mimeType = mime_type = "application/vnd.nextthought.completion.aggregatecompletionpolicy"

    def is_complete(self, progress):
        """
        Determines if the given :class:`IProgress` is enough for the item to be
        considered complete.
        """
        # If nothing set, we return True
        # If both fields are set, we check each
        result = True
        if self.count:
            result = progress.AbsoluteProgress >= self.count
        if self.percentage and result:
            if progress.MaxPossibleProgress:
                ratio = progress.AbsoluteProgress / progress.MaxPossibleProgress
                result = ratio >= self.percentage
            else:
                # This case should be avoided...
                # Required percentage but not given a denominator
                logger.warn('No MaxPossibleProgress given when computing completion (%s/%s)',
                            progress.AbsoluteProgress,
                            progress.MaxPossibleProgress)
                result = False
        return result


@interface.implementer(ICompletableItemDefaultRequiredPolicy)
class CompletableItemDefaultRequiredPolicy(PersistentCreatedAndModifiedTimeObject,
                                           SchemaConfigured):

    createDirectFieldProperties(ICompletableItemDefaultRequiredPolicy)

    mimeType = mime_type = "application/vnd.nextthought.completion.defaultrequiredpolicy"

    def __init__(self, *args, **kwargs):
        super(CompletableItemDefaultRequiredPolicy, self).__init__(*args, **kwargs)
        self.mime_types = OOTreeSet()
