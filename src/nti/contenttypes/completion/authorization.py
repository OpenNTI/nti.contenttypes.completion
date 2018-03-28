#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.security.permission import Permission

#These are registerd in configure.zcml also

ACT_VIEW_PROGRESS = Permission('nti.actions.completion.viewprogress')
ACT_LIST_PROGRESS = Permission('nti.actions.completion.listprogress')
