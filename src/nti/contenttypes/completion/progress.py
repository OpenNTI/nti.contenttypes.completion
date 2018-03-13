#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: model.py 123306 2017-10-19 03:47:14Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

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
