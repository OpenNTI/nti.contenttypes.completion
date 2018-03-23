#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

from zope import interface

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import IProgress
from nti.contenttypes.completion.interfaces import ICompletionContextProgress

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)

@WithRepr
@interface.implementer(IProgress)
class Progress(SchemaConfigured):

    createDirectFieldProperties(IProgress)

    __external_can_create__ = False

    __external_class_name__ = "Progress"
    mimeType = mime_type = "application/vnd.nextthought.completion.progress"

    last_modified = alias('LastModified')
    ntiid = alias('NTIID')

    def __init__(self, User=None, LastModified=None, *args, **kwargs):
        last_mod = LastModified
        if LastModified is not None:
            try:
                last_mod = datetime.utcfromtimestamp(LastModified)
            except TypeError:
                pass
        if User is not None:
            User = IPrincipal(User)
        kwargs['User'] = User
        kwargs['LastModified'] = last_mod
        super(Progress, self).__init__(*args, **kwargs)

    @property
    def PercentageProgress(self):
        if not self.MaxPossibleProgress:
            return 0.0
        return float(self.AbsoluteProgress) / float(self.MaxPossibleProgress)


@WithRepr
@interface.implementer(ICompletionContextProgress)
class CompletionContextProgress(Progress, SchemaConfigured):

    createDirectFieldProperties(ICompletionContextProgress)

    __external_can_create__ = False

    __external_class_name__ = "CompletionContextProgress"
    mimeType = mime_type = "application/vnd.nextthought.completion.completioncontextprogress"

    def __init__(self, *args, **kwargs):
        super(CompletionContextProgress, self).__init__(*args, **kwargs)
