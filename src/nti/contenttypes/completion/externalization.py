#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Implementations for user externalization.

.. $Id: externalization.py 124654 2017-12-07 23:45:29Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_standard_external_dictionary

from nti.externalization.interfaces import IExternalObject
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS


@component.adapter(ICompletableItemDefaultRequiredPolicy)
@interface.implementer(IExternalObject)
class _CompletableItemDefaultRequiredPolicyExternalObject(object):

    def __init__(self, policy):
        self.policy = policy

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.policy, **kwargs)
        result['mime_types'] = [to_external_object(x) for x in self.policy.mime_types]
        return result


@component.adapter(ICompletableItemContainer)
@interface.implementer(IExternalObject)
class _CompletableItemContainerExternalObject(object):

    def __init__(self, container):
        self.container = container

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.container, **kwargs)
        result['required'] = list(self.container.get_required_keys())
        result['optional'] = list(self.container.get_optional_keys())
        return result


@component.adapter(ICompletionContextCompletionPolicyContainer)
@interface.implementer(IExternalObject)
class _CompletionContextCompletionPolicyContainerExternalObject(object):

    def __init__(self, container):
        self.container = container

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.container, **kwargs)
        # TODO: Why do I have to do this?
        result['context_policy'] = to_external_object(self.container.context_policy)
        result[ITEMS] = {key:to_external_object(val) for key, val in self.container.items()}
        return result
