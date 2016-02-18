# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class DummyModel(orm.Model):
    # expect "no access rules" error
    _name = 'another.dummy.model'
    _columns = {
        'name': fields.char('Dummy', size=100),
    }
