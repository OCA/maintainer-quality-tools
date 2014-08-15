# -*- coding: utf-8 -*-

from openerp.osv import fields, orm


class DummyModel(orm.Model):
    # expect "no access rules" error
    _name = 'dummy.model'
    _columns = {
        'name': fields.char('Dummy', size=100),
    }


# printout non-ASCII text to check unicode issues
# (from Monty Python's "Italian Lesson"...)
print("Eeeeeee! Milano è tanto meglio di Napoli. "
      "Milano è la citta la più bella di tutti ... nel mondo...")
