# coding: utf-8

from openerp import fields, models
from openerp.tools.translate import _


class MyExampleField(models.Model):
    _name = "my.example.field"
    name = fields.Char(_('Title'), size=100)
    description = fields.Char(string=_('Description'), size=100)


class MyExampleField2(models.Model):
    _name = "my.example.field2"

    name = fields.Char(_('Title'), size=100)
    description = fields.Char(name=_('Description'), size=100)

    def my_method1(self, var):
        pass

    def my_method2(self):
        return self.my_method1(_('Hello world'))
