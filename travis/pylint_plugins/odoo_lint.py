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
    # ODOO checkers type
    #  C: convention
    #  R: refactor
    #  W: warning
    #  E: error
    #  F: fatal
    # ODOO globals checkers id:
    #  (Use this value in all class of odoo-lint)
    #  O
    # ODOO global checkers class:
    #  (don't use other value in this class)
    #  0
    # ODOO checkers method:
    #  00 (2 digits from 00 to 99)
    # Message code of example:
    #  In this class: WO-0-00, EO-0-00
    #  OTHER CLASS: WO-1-00, EO-1-00

    'CO001': (
        'Missing icon ./static/description/icon.png',
        'missing-icon',  # Name used to found check method.
        MSG_TMPL,
    ),
    'CO002': (
        'Documentation ./doc/index.rst is missing',
        'missing-doc',
        MSG_TMPL,
    ),
    'CO006': (
        'Missing required %s keys in manifest file __openerp__.py',
        'manifest-missing-key',
        MSG_TMPL,
    ),
    'CO003': (
        'Missing ./README.rst file. Template here: %s',
        'missing-readme',
        MSG_TMPL,
    ),
    'CO004': (
        'Deprecated description in manifest file __openerp__.py',
        'deprecated-description',
        MSG_TMPL,
    ),
    'CO005': (
        'Missing author required "%s"',
        'missing-required-author',
        MSG_TMPL,
    ),
    'EO002': (
        'Syntax error in file ./README.rst',
        'readme-syntax-error',
        MSG_TMPL,
    ),
    'EO003': (
        'Syntax error in file ./doc/index.rst',
        'doc-syntax-error',
        MSG_TMPL,
    ),
    'EO001': (
        'Syntax error in manifest file __openerp__.py',
        'manifest-syntax-error',
        MSG_TMPL,
    ),
}


PY_MODULE_MSGS = {
    # Messages that visit module but don't require a odoo module
    'WO001': (
        'Missing coding comment',
        'missing-coding-comment',
        'More info here: '
        'https://www.python.org/dev/peps/pep-0263/' +
        (MSG_TMPL or '')
    ),
    'CO007': (
        'No UTF-8 coding found: Use `# -*- coding: utf-8 -*-` '
        'in first or second line of your file.',
        'no-utf8-coding-comment',
        MSG_TMPL
    ),
    'WO002': (
        'Unexpected interpreter comment and execute permissions. '
        'Interpreter: %s Exec perm: %s',
        'unexpected-interpreter-exec-perm',
        MSG_TMPL
    ),
}

PY_MSGS = {
    # Messages that don't use visit module method
    'RO001': (
        'Import `Warning` should be renamed as UserError '
        '`from openerp.exceptions import Warning as UserError`',
        'openerp-exception-warning',
        MSG_TMPL
    ),
    'WO003': (
        'Detected api.one and api.multi decorators together.',
        'api-one-multi-together',
        MSG_TMPL
    ),
    'WO004': (
        'Missing api.one in copy function.',
        'copy-wo-api-one',
        MSG_TMPL
    ),
}


def add_msg(f):
    def decorator_add_msg(self, node=None):
        '''Decorator method a decorator to add a msg if the original method
        returned a negative value then add message.
        Use object attributes called:
            - name_key: Required string name of message to add.
            - msg_args: Tuple with arguments to use in msg.
                default: None
        :param node: node astroid standard parameter
            If original method don't receive then
            try to get from original object `self.node`
        '''
        if node is None:
            node = getattr(self, 'node', None)
        name_key = getattr(self, 'name_key', None)
        assert node is not None, "self.node variable not defined"
        assert name_key, "self.name_key variable not defined"
        res = f(self)
        msg_args = getattr(self, 'msg_args', None)
        if not res:
            self.add_message(name_key, node=node,
                             args=msg_args)
        # clean buffer of optional variable
        self.msg_args = None
    return decorator_add_msg


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

    msgs = ODOO_MODULE_MSGS.copy()
    msgs.update(PY_MSGS)
    msgs.update(PY_MODULE_MSGS)

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

    def get_interpreter_and_coding(self):
        """Get '#!/bin' comment and '# -*- coding:' comment.
        :return: Return a tuple with two string
            (interpreter_bin, coding_comment)
            if not found then use empty string
        """
        interpreter_bin = ''
        coding_comment = ''
        with self.node.file_stream as fstream:
            cont = 0
            for line in fstream:
                cont += 1
                if "#!" == line[:2]:
                    interpreter_bin = line.strip('\n')
                if "# -*- coding: " in line:
                    coding_comment = line.strip('\n')
                if cont == 2:
                    break
        return interpreter_bin, coding_comment

    def get_decorators_names(self, decorators):
        nodes = []
        if decorators:
            nodes = decorators.nodes
        return [getattr(decorator, 'attrname', '')
                for decorator in nodes if decorator is not None]

    @utils.check_messages('api-one-multi-together',
                          'copy-wo-api-one')
    def visit_function(self, node):
        '''Enable next checks:
            Check api.one and api.multi together
            Method copy without api.one
        '''
        decor_names = self.get_decorators_names(node.decorators)
        decor_lastnames = [
            decor.split('.')[-1]
            for decor in decor_names]
        if self.linter.is_message_enabled('api-one-multi-together'):
            if 'one' in decor_lastnames \
                    and 'multi' in decor_lastnames:
                self.add_message('api-one-multi-together',
                                 node=node)

        if self.linter.is_message_enabled('copy-wo-api-one'):
            if 'copy' == node.name and 'one' not in decor_lastnames:
                self.add_message('copy-wo-api-one', node=node)

    @utils.check_messages('openerp-exception-warning')
    def visit_from(self, node):
        if node.modname == 'openerp.exceptions':
            for (import_name, import_as_name) in node.names:
                if import_name == 'Warning' \
                        and import_as_name != 'UserError':
                    self.add_message(
                        'openerp-exception-warning', node=node)

    @add_msg
    def _check_unexpected_interpreter_exec_perm(self):
        interpreter_bin, coding = self.get_interpreter_and_coding()
        access_x_ok = os.access(self.node.file, os.X_OK)
        self.msg_args = (interpreter_bin, access_x_ok)
        return bool(interpreter_bin) == access_x_ok

    @add_msg
    def _check_no_utf8_coding_comment(self):
        'Check that the coding utf-8 comment exists'
        interpreter_bin, coding = self.get_interpreter_and_coding()
        if not coding:
            return True
        if coding == '# -*- coding: utf-8 -*-':
            return True
        return False

    @add_msg
    def _check_missing_coding_comment(self):
        'Check that the coding comment exists.'
        interpreter_bin, coding = self.get_interpreter_and_coding()
        if coding:
            return True
        return False

    @utils.check_messages(
        *(ODOO_MODULE_MSGS.keys() + PY_MODULE_MSGS.keys()))
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
        self.module_path = os.path.dirname(node.file)
        self.node = node
        for msg_code, (title, name_key, description) in \
                sorted(self.msgs.iteritems()):
            if not self.linter.is_message_enabled(name_key):
                continue
            check_method = getattr(
                self, '_check_' + name_key.replace('-', '_'),
                None)
            self.name_key = msg_code
            if callable(check_method):
                self.manifest_file = None
                self.manifest_content = None
                if odoo_files:
                    self.manifest_file = os.path.join(
                        self.module_path, odoo_files[0])
                    self.manifest_content = open(self.manifest_file).read()
                elif msg_code in ODOO_MODULE_MSGS.keys():
                    # If is a check of odoo_module
                    # but no is odoo module
                    continue
                check_method()

    @add_msg
    def _check_missing_icon(self):
        """Check if a odoo module has a icon image
        :return: True if icon is found else False.
        """
        icon_path = os.path.join(
            self.module_path, 'static', 'description', 'icon.png')
        return os.path.isfile(icon_path)

    def get_doc_path(self):
        doc_path = os.path.join(
            self.module_path, 'doc', 'index.rst')
        if os.path.isfile(doc_path):
            return doc_path
        return False

    @add_msg
    def _check_missing_doc(self):
        '''
        Check if the module has a ./doc/index.rst file
        :return: If exists return full path else False
        '''
        return self.get_doc_path()

    @add_msg
    def _check_doc_syntax_error(self):
        '''
        Check syntaxis of ./doc/index.rst file with `rst2html`
        :return: if has syntaxis error return False
            else True but if don't exists file return True
        '''
        fpath = self.get_doc_path()
        if not fpath:
            return True
        return self.check_rst_syntax(fpath)

    def get_manifest_dict(self):
        try:
            manifest_dict = eval(self.manifest_content)
        except BaseException:  # Why can be any exception
            manifest_dict = None
        return manifest_dict

    @add_msg
    def _check_manifest_syntax_error(self):
        '''
        Check any exception in `self.manifest_content`
        :return: manifest content dict if no errors else None
        '''
        return self.get_manifest_dict()

    @add_msg
    def _check_manifest_missing_key(self):
        '''Check if a required key is missing in manifest file
        :return: False if key required is missing else True
        '''
        manifest_dict = self.get_manifest_dict()
        if not manifest_dict:
            return True
        required_keys = self.config.manifest_required_keys
        self.msg_args = (required_keys,)
        return set(required_keys).issubset(
            set(manifest_dict.keys()))

    def get_readme_path(self):
        readme_path = os.path.join(
            self.module_path, 'README.rst')
        if os.path.isfile(readme_path):
            return readme_path
        return False

    @add_msg
    def _check_missing_readme(self):
        '''
        Check if the module has a ./README.rst file
        :return: If exists return full path else False
        '''
        readme_path = self.get_readme_path()
        if not readme_path:
            self.msg_args = (self.config.readme_template_url,)
            return False
        return True

    @add_msg
    def _check_readme_syntax_error(self):
        '''
        Check syntaxis of ./README.rst file with `rst2html`
        :return: if has syntaxis error return False
            else True but if don't exists file return True
        '''
        fpath = self.get_readme_path()
        if not fpath:
            return True
        return self.check_rst_syntax(fpath)

    @add_msg
    def _check_deprecated_description(self):
        '''Check if description is defined in manifest file
        :return: False if is defined else True
        '''
        manifest_dict = self._check_manifest_syntax_error()
        if not manifest_dict:
            return True
        return 'description' not in manifest_dict

    @add_msg
    def _check_missing_required_author(self):
        '''Check if manifest file has required author
        :return: True if is found it else False'''
        manifest_dict = self.get_manifest_dict()
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
