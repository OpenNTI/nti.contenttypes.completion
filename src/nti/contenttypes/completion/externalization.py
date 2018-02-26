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

from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy

from nti.externalization.externalization import to_external_object
from nti.externalization.externalization import to_standard_external_dictionary

from nti.externalization.interfaces import IExternalObject


@component.adapter(ICompletableItemDefaultRequiredPolicy)
@interface.implementer(IExternalObject)
class _CompletableItemDefaultRequiredPolicyExternalObject(object):

    def __init__(self, policy):
        self.policy = policy

    def toExternalObject(self, **kwargs):
        result = to_standard_external_dictionary(self.policy, **kwargs)
        result['mime_types'] = [to_external_object(x) for x in self.policy.mime_types]
        return result
