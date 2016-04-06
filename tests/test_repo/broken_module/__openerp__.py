# -*- coding: utf-8 -*-
{
    'name': 'Broken module for tests',
    # missing license
    'author': 'Many People',  # Missing oca author
    'description': 'Should be a README.rst file',
    'version': '1.0',  # wrong version format
    'depends': ['base'],
    'data': ['model_view.xml',
             'security/ir.model.access.csv'],
    'test': ['test.yml'],
    'installable': True,
    'name': 'Duplicated value',
    'active': True,  # Deprecated active key
}
