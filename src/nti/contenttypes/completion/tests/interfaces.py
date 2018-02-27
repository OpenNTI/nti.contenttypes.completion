#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope.security.interfaces import IPrincipal

from nti.contenttypes.completion.interfaces import ICompletableItem
from nti.contenttypes.completion.interfaces import ICompletionContext


class ITestPrincipal(IPrincipal):
    """
    A interface for items that may be completable once certain conditions are
    met.
    """


class ITestCompletableItem(ICompletableItem):
    """
    A interface for items that may be completable once certain conditions are
    met.
    """


class ITestCompletionContext(ICompletionContext):
    """
    A test completion context interface.
    """
