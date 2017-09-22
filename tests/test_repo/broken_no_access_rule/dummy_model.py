# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp import fields


class DummyModel(orm.Model):
    # expect "no access rules" error
    _name = 'another.dummy.model'
    name = fields.Char('Dummy', size=100)
