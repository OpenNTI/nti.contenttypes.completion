#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
from datetime import datetime

from zope import interface

from zope.component import queryMultiAdapter

from zope.interface import providedBy

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import ICompletionContextCompletionPolicy
from nti.contenttypes.completion.interfaces import ICompletionContextProgress
from nti.contenttypes.completion.interfaces import ICompletedItem
from nti.contenttypes.completion.interfaces import ICourseCompletionProgress

from nti.contenttypes.completion.interfaces import IProgress

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
        try:
            result = float(self.AbsoluteProgress) / float(self.MaxPossibleProgress)
        except (TypeError, ZeroDivisionError):
            result = None
        return result


@WithRepr
@interface.implementer(ICompletionContextProgress)
class CompletionContextProgress(Progress, SchemaConfigured):

    createDirectFieldProperties(ICompletionContextProgress)

    __external_can_create__ = False

    __external_class_name__ = "CompletionContextProgress"
    mimeType = mime_type = "application/vnd.nextthought.completion.completioncontextprogress"

    def __init__(self, *args, **kwargs):
        super(CompletionContextProgress, self).__init__(*args, **kwargs)


@interface.implementer(ICourseCompletionProgress)
class CourseCompletionProgressFactory(object):

    def __init__(self, user, course):
        self.user = user
        self.course = course

    def course_completion(self):
        """
        Returns Unicode N/a if a completion policy does not exist
        Returns Unicode 0 if the course progress is undefined
        Returns Unicode completion percentage if the course is not completed
        Returns Unicode date of completion if the course is complete
        """

        user = self.user
        course = self.course

        try:
            completion_policy = ICompletionContextCompletionPolicy(course)
        except TypeError:
            return u'N/A'

        progress = queryMultiAdapter((user, course), IProgress)

        # Progress is undefined, completion is 0
        if not progress:
            return u'0'

        completion = six.text_type(progress.PercentageProgress)

        completion_item = completion_policy.is_complete(progress)

        # The course is not yet completed, therefore completion is a percentage
        if not completion_item:
            return completion

        if ICompletedItem is providedBy(completion_item) and completion_item.CompletedDate:
            return six.text_type(completion_item.CompletedDate)
