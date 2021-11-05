#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.externalization.datastructures import InterfaceObjectIO

from nti.contenttypes.completion.interfaces import IAwardedCompletedItem

class AwardedCompletedItemIO(InterfaceObjectIO):

    __allowed_keys__ = frozenset({'Principal', 'Item'})

    _ext_iface_upper_bound = IAwardedCompletedItem

    def _ext_accept_update_key(self, k, ext_self, ext_keys):
        return k in self.__allowed_keys__ \
            or InterfaceObjectIO._ext_accept_update_key(self, k, ext_self, ext_keys)
