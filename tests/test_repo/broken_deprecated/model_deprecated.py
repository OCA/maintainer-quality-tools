# -*- coding: utf-8 -*-

# This file is not imported by odoo
# to compatibility with real deprecated versions

from openerp.osv import osv  # pylint: disable=W0403


class DeprecatedOsvOsv(osv.osv):
    _name = 'deprecated.osv'


class DeprecatedOsvOsvMemory(osv.osv_memory):
    _name = 'deprecated.osv_memory'
