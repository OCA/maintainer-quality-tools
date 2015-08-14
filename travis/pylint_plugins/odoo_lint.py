# ~/.local/lib/python2.7/site-packages/odoolint.py

import os
import subprocess

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker
from pylint.checkers import utils


MANIFEST_FILES = ['__odoo__.py', '__openerp__.py', '__terp__.py']
MANIFEST_REQUIRED_KEYS = ['name', 'license']
AUTHOR_REQUIRED = 'Odoo Community Association (OCA)'
MSG_GUIDELINES = 'You can review guidelines here: ' + \
    'https://github.com/OCA/maintainer-tools/blob/' + \
    'master/CONTRIBUTING.md'
MSG_TMPL = '{msg_guidelines}'  # Require {msg_guidelines}
README_TMPL_URL = 'https://github.com/OCA/maintainer-tools' + \
    '/blob/master/template/module/README.rst'
ODOO_MODULE_MSGS = {
    #  and WO for warnings from odoo_lint
    'WO010': (
        'Missing icon ./static/description/icon.png',
        'missing-icon',  # Name used to found check method.
        MSG_TMPL,
    ),
    'WO020': (
        'Documentation ./doc/index.rst is missing',
        'missing-doc',
        MSG_TMPL,
    ),
    'WO030': (
        'Missing required %s keys in manifest file __openerp__.py',
        'manifest-missing-key',
        MSG_TMPL,
    ),
    'WO040': (
        'Missing ./README.rst file. Template here: %s',
        'missing-readme',
        MSG_TMPL,
    ),
    'WO050': (
        'Deprecated description in manifest file __openerp__.py',
        'deprecated-description',
        MSG_TMPL,
    ),
    'WO060': (
        'Missing author required "%s"',
        'missing-required-author',
        MSG_TMPL,
    ),
    'EO030': (
        'Syntax error in file ./README.rst',
        'readme-syntax-error',
        MSG_TMPL,
    ),
    'EO020': (
        'Syntax error in file ./doc/index.rst',
        'doc-syntax-error',
        MSG_TMPL,
    ),
    'EO010': (
        'Syntax error in manifest file __openerp__.py',
        'manifest-syntax-error',
        MSG_TMPL,
    ),
}


class OdooLintAstroidChecker(BaseChecker):

    __implements__ = IAstroidChecker

    # configuration section name
    name = 'odoolint'

    options = (('manifest_author_required',
                {'type': 'string',
                 'metavar': '<string>',
                 'default': AUTHOR_REQUIRED,
                 'help': 'Name of author required in manifest ' +
                         'file __odoo__.py.'
                 }),
               ('manifest_required_keys',
                {
                    'type': 'csv',
                    'metavar': '<comma separated values>',
                    'default': MANIFEST_REQUIRED_KEYS,
                    'help': 'List of keys required in manifest ' +
                            'odoo file __openerp__.py, ' +
                            'separated by a comma.'
                }),
               ('msg_guidelines',
                {
                    'type': 'string',
                    'metavar': '<comma separated values>',
                    'default': MSG_GUIDELINES,
                    'help': 'Message of guidelines to show with ' +
                            '--help-msg=<msg_id> param.',
                }),
               ('readme_template_url',
                {
                    'type': 'string',
                    'metavar': '<string>',
                    'default': README_TMPL_URL,
                    'help': 'URL of README.rst template file',
                }),
               )

    msgs = ODOO_MODULE_MSGS

    def add_msg_guidelines(self, msg_guidelines):
        new_msgs = {}
        for msg_code, (title, name_key, description) in \
                self.msgs.iteritems():
            new_msgs[msg_code] = (
                title, name_key,
                description.format(msg_guidelines=msg_guidelines))
        self.msgs = new_msgs

    def __init__(self, linter=None):
        BaseChecker.__init__(self, linter)
        self.add_msg_guidelines(self.config.msg_guidelines)

    def is_odoo_module(self, module_file):
        '''Check if directory of py module is a odoo module too.
        if exists a MANIFEST_FILES is a odoo module.
        :param module_file: String with full path of a
            python module file.
            If is a folder py module then will receive
                `__init__.py file path.
            A normal py file is a module too.
        :return: List of names files with match to MANIFEST_FILES
        '''
        return os.path.basename(module_file) == '__init__.py' and \
            [
                filename
                for filename in os.listdir(
                    os.path.dirname(module_file))
                if filename in MANIFEST_FILES
            ]

    def check_rst_syntax(self, fname):
        '''Check syntax in rst files.
        :param fname: String with file name path to check
        :return: False if fname has errors else True
        '''
        cmd = ['rst2html.py', fname, '/dev/null', '-r', '1']
        errors = subprocess.Popen(
            cmd, stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE).stdout.read()
        if errors:
            return False
        return True

    @utils.check_messages(*(ODOO_MODULE_MSGS.keys()))
    def visit_module(self, node):
        '''
        Call methods named with name_key from ODOO_MODULE_MSGS
        Method should be named with next standard:
            def _check_{MSG_NAME_KEY}(self, module_path)
        by example: def _check_missing_icon(self, module_path)
                    to check missing-icon message name key
        And should return True if all fine else False.
        If is false then method of pylint add_message will invoke
        You can use `self.module_path` variable in those methods
            to get full path of odoo module directory.
        You can use `self.manifest_file` variable in those methods
            to get full path of MANIFEST_FILE found (__openerp__.py)
        You can use `self.manifest_content` variable in those methods
            to get full content of MANIFEST_FILE found.
        :param node: A astroid.scoped_nodes.Module from visit*
            standard method of pylint.
        :return: None
        '''
        odoo_files = self.is_odoo_module(node.file)
        if odoo_files:
            self.module_path = os.path.dirname(node.file)
            self.manifest_file = os.path.join(
                self.module_path, odoo_files[0])
            self.manifest_content = open(self.manifest_file).read()
            for msg_code, (title, name_key, description) in \
                    sorted(self.msgs.iteritems()):
                check_method = getattr(
                    self, '_check_' + name_key.replace('-', '_'))
                self.msg_args = None
                if not check_method():
                    self.add_message(name_key, node=node,
                                     args=self.msg_args)

    def _check_missing_icon(self):
        """Check if a odoo module has a icon image
        :return: True if icon is found else False.
        """
        icon_path = os.path.join(
            self.module_path, 'static', 'description', 'icon.png')
        return os.path.isfile(icon_path)

    def _check_missing_doc(self):
        '''
        Check if the module has a ./doc/index.rst file
        :return: If exists return full path else False
        '''
        doc_path = os.path.join(
            self.module_path, 'doc', 'index.rst')
        if os.path.isfile(doc_path):
            return doc_path
        return False

    def _check_doc_syntax_error(self):
        '''
        Check syntaxis of ./doc/index.rst file with `rst2html`
        :return: if has syntaxis error return False
            else True but if don't exists file return True
        '''
        fpath = self._check_missing_doc()
        if not fpath:
            return True
        return self.check_rst_syntax(fpath)

    def _check_manifest_syntax_error(self):
        '''
        Check any exception in `self.manifest_content`
        :return: manifest content dict if no errors else None
        '''
        try:
            manifest_dict = eval(self.manifest_content)
        except BaseException:  # Why can be any exception
            manifest_dict = None
        return manifest_dict

    def _check_manifest_missing_key(self):
        '''Check if a required key is missing in manifest file
        :return: False if key required is missing else True
        '''
        manifest_dict = self._check_manifest_syntax_error()
        if not manifest_dict:
            return True
        required_keys = self.config.manifest_required_keys
        self.msg_args = (required_keys,)
        return set(required_keys).issubset(
            set(manifest_dict.keys()))

    def _check_missing_readme(self):
        '''
        Check if the module has a ./README.rst file
        :return: If exists return full path else False
        '''
        readme_path = os.path.join(
            self.module_path, 'README.rst')
        if os.path.isfile(readme_path):
            return readme_path
        self.msg_args = (self.config.readme_template_url,)
        return False

    def _check_readme_syntax_error(self):
        '''
        Check syntaxis of ./README.rst file with `rst2html`
        :return: if has syntaxis error return False
            else True but if don't exists file return True
        '''
        fpath = self._check_missing_readme()
        if not fpath:
            return True
        return self.check_rst_syntax(fpath)

    def _check_deprecated_description(self):
        '''Check if description is defined in manifest file
        :return: False if is defined else True
        '''
        manifest_dict = self._check_manifest_syntax_error()
        if not manifest_dict:
            return True
        return 'description' not in manifest_dict

    def _check_missing_required_author(self):
        '''Check if manifest file has required author
        :return: True if is found it else False'''
        manifest_dict = self._check_manifest_syntax_error()
        if not manifest_dict:
            return True
        authors = manifest_dict.get('author', '').split(',')
        author_required = self.config.manifest_author_required
        for author in authors:
            if author_required in author:
                return True
        self.msg_args = (author_required,)
        return False


def register(linter):
    """Required method to auto register this checker"""
    linter.register_checker(OdooLintAstroidChecker(linter))
