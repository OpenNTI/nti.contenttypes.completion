#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: internalization.py 122560 2017-09-30 23:21:05Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS

logger = __import__('logging').getLogger(__name__)


@component.adapter(ICompletableItemDefaultRequiredPolicy)
@interface.implementer(IInternalObjectUpdater)
class _CompletableItemDefaultRequiredPolicyUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        """
        Make sure we store these objects in the container we choose. IO, by
        default will store in a list.
        """
        mime_container = type(self.obj.mime_types)
        interface_io = InterfaceObjectIO(self.obj,
                                        ICompletableItemDefaultRequiredPolicy)
        result = interface_io.updateFromExternalObject(parsed, *args, **kwargs)
        new_mime_container = mime_container()
        new_mime_container.update(self.obj.mime_types)
        self.obj.mime_types = new_mime_container
        return result
