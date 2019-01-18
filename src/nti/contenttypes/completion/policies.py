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

from nti.contenttypes.completion.completion import CompletedItem

from nti.contenttypes.completion.interfaces import ICompletionContext
from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemAggregateCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyFactory
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyConfigurationUtility

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.datastructures import InterfaceObjectIO

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.eqhash import EqHash

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@interface.implementer(ICompletableItemCompletionPolicy)
class AbstractCompletableItemCompletionPolicy(PersistentCreatedAndModifiedTimeObject,
                                              SchemaConfigured,
                                              Contained):
    createDirectFieldProperties(ICompletableItemCompletionPolicy)


class AbstractCompletableItemCompletionPolicyIO(InterfaceObjectIO):
    """
    Non-persistent subclasses of AbstractCompletableItemCompletionPolicy would
    rely on this IO for externalization.
    """
    _ext_iface_upper_bound = ICompletableItemCompletionPolicy


@EqHash('percentage')
@interface.implementer(ICompletableItemAggregateCompletionPolicy)
class CompletableItemAggregateCompletionPolicy(AbstractCompletableItemCompletionPolicy):
    createDirectFieldProperties(ICompletableItemAggregateCompletionPolicy)

    mimeType = mime_type = "application/vnd.nextthought.completion.aggregatecompletionpolicy"

    creator = None

    def is_complete(self, progress):
        """
        Determines if the given :class:`IProgress` is enough for the item to be
        considered complete.
        """
        result = None
        if self.percentage:
            if progress is not None and progress.MaxPossibleProgress:
                ratio = progress.AbsoluteProgress / progress.MaxPossibleProgress
                if ratio >= self.percentage:
                    success = bool(not getattr(progress, 'UnsuccessfulItemNTIIDs', ()))
                    result = CompletedItem(Item=progress.Item,
                                           Principal=progress.User,
                                           CompletedDate=progress.LastModified,
                                           Success=success)
            else:
                # This case should be avoided...
                # Required percentage but not given a denominator
                if progress is not None:
                    logger.warning('No MaxPossibleProgress given when computing completion (%s/%s)',
                                   progress.AbsoluteProgress,
                                   progress.MaxPossibleProgress)
        return result


@interface.implementer(ICompletionContextCompletionPolicyFactory)
class CompletionContextCompletionPolicyFactory(SchemaConfigured):
    """
    A :class:`ICompletionContextCompletionPolicyFactory` that returns a default
    100% :class:`ICompletableItemAggregateCompletionPolicy`.
    """
    createDirectFieldProperties(ICompletionContextCompletionPolicyFactory)

    def __call__(self):
        return CompletableItemAggregateCompletionPolicy()


@interface.implementer(ICompletionContextCompletionPolicyFactory)
class NoOpCompletionContextCompletionPolicyFactory(SchemaConfigured):
    """
    A :class:`ICompletionContextCompletionPolicyFactory` that returns no
    policy, for those sites that do not want completion by default.
    """
    createDirectFieldProperties(ICompletionContextCompletionPolicyFactory)

    def __call__(self):
        return None


@interface.implementer(ICompletionContextCompletionPolicyConfigurationUtility)
class DefaultCompletionPolicyConfigurationUtility(object):

    def is_editting_completion_policy_open(self, completion_context):
        return ICompletionContext.providedBy(completion_context)
