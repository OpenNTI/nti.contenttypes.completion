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

from nti.contenttypes.completion.interfaces import ICompletableItemContainer
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletableItemDefaultRequiredPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicyContainer

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater
from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for
from nti.externalization.internalization import update_from_external_object

from nti.ntiids.ntiids import find_object_with_ntiid

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
        updated = False
        if "mime_types" in parsed:
            self.obj.set_mime_types(parsed.pop('mime_types') or ())
            updated = True

        interface_io = InterfaceObjectIO(self.obj,
                                         ICompletableItemDefaultRequiredPolicy)
        return interface_io.updateFromExternalObject(parsed, *args, **kwargs) or updated


@component.adapter(ICompletableItemContainer)
@interface.implementer(IInternalObjectUpdater)
class _CompletableItemContainerUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = ICompletableItemContainer

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        """
        Make sure we store these objects in the container we choose. IO, by
        default will store in a list.
        """
        result = super(_CompletableItemContainerUpdater,self).updateFromExternalObject(parsed, *args, **kwargs)
        required = parsed.get('required') or ()
        optional = parsed.get('optional') or ()
        for required_ntiid in required:
            obj = find_object_with_ntiid(required_ntiid)
            if obj is None:
                logger.warning('Cannot find required object (%s)',
                               required_ntiid)
                continue
            self._ext_self.add_required_item(obj)
        for optional_ntiid in optional:
            obj = find_object_with_ntiid(optional_ntiid)
            if obj is None:
                logger.warning('Cannot find optional object (%s)',
                               optional_ntiid)
                continue
            self._ext_self.add_optional_item(obj)
        return result


@component.adapter(ICompletionContextCompletionPolicyContainer)
@interface.implementer(IInternalObjectUpdater)
class _CompletionContextCompletionPolicyContainerUpdater(InterfaceObjectIO):

    _ext_iface_upper_bound = ICompletionContextCompletionPolicyContainer

    def updateFromExternalObject(self, parsed, *args, **kwargs):
        """
        Make sure we store these objects in the container we choose. IO, by
        default will store in a list.
        """
        result = super(_CompletionContextCompletionPolicyContainerUpdater, self).updateFromExternalObject(parsed, *args, **kwargs)
        container = parsed.get(ITEMS) or {}
        for container_key, policy in container.items():
            obj = find_object_with_ntiid(container_key)
            if obj is None:
                logger.warning('Cannot find object with ntiid for policy (%s)',
                               container_key)
                continue
            factory = find_factory_for(policy)
            policy_obj = factory()
            update_from_external_object(policy_obj, policy)
            self._ext_self[container_key] = policy_obj
        if self._ext_self.context_policy is not None:
            # Set completion context policy features
            interface.alsoProvides(self._ext_self.context_policy,
                                   ICompletionContextCompletionPolicy)
            self._ext_self.context_policy.__parent__ = self._ext_self
        return result
