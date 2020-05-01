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

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IProgress)
class Progress(object):
    # There are use cases where lots of these may be created. Therefore,
    # we skip SchemaConfigured here to improve throughput. We're responsible
    # for setting our defaults and any validation. Since these are only built
    # internally, we at least have control over our fate.

    __external_can_create__ = False

    __external_class_name__ = "Progress"
    mimeType = mime_type = "application/vnd.nextthought.completion.progress"

    last_modified = alias('LastModified')
    ntiid = alias('NTIID')

    def __init__(self, User=None, LastModified=None, AbsoluteProgress=None,
                 MaxPossibleProgress=None, HasProgress=False, NTIID=None,
                 Item=None, CompletionContext=None):
        last_mod = LastModified
        if LastModified is not None:
            try:
                last_mod = datetime.utcfromtimestamp(LastModified)
            except TypeError:
                pass
        if User is not None:
            User = IPrincipal(User)
        self.User = User
        self.LastModified = last_mod
        self.AbsoluteProgress = AbsoluteProgress
        self.MaxPossibleProgress = MaxPossibleProgress
        self.HasProgress = HasProgress
        self.NTIID = NTIID
        self.Item = Item
        self.CompletionContext = CompletionContext

    @property
    def PercentageProgress(self):
        try:
            result = float(self.AbsoluteProgress) / float(self.MaxPossibleProgress)
        except (TypeError, ZeroDivisionError, AttributeError):
            result = None
        return result


@WithRepr
@interface.implementer(ICompletionContextProgress)
class CompletionContextProgress(Progress):

    __external_can_create__ = False

    __external_class_name__ = "CompletionContextProgress"
    mimeType = mime_type = "application/vnd.nextthought.completion.completioncontextprogress"

    def __init__(self, CompletedItem=None, UnsuccessfulItemNTIIDs=None,
                 IncompleteItemNTIIDs=None, *args, **kwargs):
        super(CompletionContextProgress, self).__init__(*args, **kwargs)
        self.CompletedItem = CompletedItem
        self.UnsuccessfulItemNTIIDs = UnsuccessfulItemNTIIDs
        self.IncompleteItemNTIIDs = IncompleteItemNTIIDs

    @property
    def Completed(self):
        # pylint: disable=no-member
        return self.CompletedItem is not None

    @property
    def CompletedDate(self):
        # pylint: disable=no-member
        return getattr(self.CompletedItem, 'CompletedDate', None)
