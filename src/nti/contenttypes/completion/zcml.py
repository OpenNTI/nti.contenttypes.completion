#!/usr/bin/env python
# -*- coding: utf-8 -*

from zope import interface

from zope.component.zcml import adapter

from zope.configuration.fields import GlobalInterface

from nti.schema.field import Number

from nti.contenttypes.completion.interfaces import ICompletableItemCompletionPolicy

from nti.contenttypes.completion.policies import CompletableItemAggregateCompletionPolicy

logger = __import__('logging').getLogger(__name__)


class IRegisterCompletionPolicy(interface.Interface):

    percentage = Number(title=u"Percentage",
                        description=u"""The percentage of progress that must
                        be made for this context to be considered complete.""",
                        required=True,
                        min=0.0,
                        max=1.0,
                        default=1.0)

    for_ = GlobalInterface(title=u"The provided type",
                           required=True)


def registerCompletionPolicy(_context, for_=None, percentage=None):
    """
    Register a completion policy.
    """
    def initialize(unused_item):
        policy = CompletableItemAggregateCompletionPolicy()
        policy.percentage = percentage
        return policy

    adapter(_context,
            provides=ICompletableItemCompletionPolicy,
            for_=(for_,),
            factory=(initialize,))
