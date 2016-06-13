# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class Lang(orm.Model):
    # expect "redefinition of field" error
    _inherit = 'res.lang'
    _columns = {
        'name': fields.char('Resize char', size=1),
        'direction': fields.integer('Char to int'),
        'translatable': fields.selection([('value1', 'Value1')],
                                         'Boolean to selection'),
        'code': fields.text('Char to text'),
    }
