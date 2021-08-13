#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Zope vocabularies relating to capabilities.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from zope.componentvocabulary.vocabulary import UtilityNames
from zope.componentvocabulary.vocabulary import UtilityVocabulary

from zope.schema.interfaces import IVocabularyFactory

from nti.contenttypes.completion.interfaces import ICertificateRenderer

logger = __import__('logging').getLogger(__name__)


@interface.provider(IVocabularyFactory)
class CertificateRendererNameTokenVocabulary(UtilityNames):

    # This one is 'live"
    def __init__(self, *unused_args, **unused_kwargs):
        # any context argument is ignored. It is to support the
        # VocabularyFactory interface
        UtilityNames.__init__(self, ICertificateRenderer)


class CertificateRendererUtilityVocabulary(UtilityVocabulary):
    # This one enumerates at instance creation time
    interface = ICertificateRenderer


class CertificateRendererNameVocabulary(CertificateRendererUtilityVocabulary):
    nameOnly = True
