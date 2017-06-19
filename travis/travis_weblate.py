#!/usr/bin/env python
# coding: utf-8

import os
import re
import glob
import subprocess

from odoo_connection import Odoo10Context, context_mapping
from test_server import (get_addons_path, get_server_path, parse_list)
from apis import ApiException, WeblateApi, GitHubApi
from travis_helpers import yellow
from git_run import GitRun


class TravisWeblateUpdate(object):

    GIT_COMMIT_INFO = {
        'author': 'Weblate bot <weblate@bot>',
        'message': '[REF] i18n: Updating translation terms from weblate '
                   '[ci skip]'
    }

    def __init__(self):
        self._git = GitRun(os.path.join(os.getcwd(), '.git'), True)
        self.branch = os.environ.get("TRAVIS_BRANCH",
                                     self._git.get_branch_name())
        remote = self._git.run(["ls-remote", "--get-url", "origin"])
        name = remote.replace(':', '/')
        name = re.sub('.+@', '', name)
        name = re.sub('.git$', '', name)
        name = re.sub('^https://', '', name)
        name = re.sub('^http://', '', name)
        match = re.search(
            r'(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+)', name)
        if match:
            name = ("%(host)s:%(owner)s/%(repo)s (%(branch)s)" %
                    dict(match.groupdict(), branch=self.branch))
        self.repo_name = name
        self.wl_api = WeblateApi()
        self.gh_api = GitHubApi()
        self._travis_home = os.environ.get("HOME", "~/")
        self._travis_build_dir = os.environ.get("TRAVIS_BUILD_DIR", "../..")
        self._odoo_version = os.environ.get("VERSION")
        self._odoo_branch = os.environ.get("ODOO_BRANCH")
        self._langs = (parse_list(os.environ.get("LANG_ALLOWED")) if
                       os.environ.get("LANG_ALLOWED", False) else [])
        self._odoo_full = os.environ.get("ODOO_REPO", "odoo/odoo")
        self._server_path = get_server_path(self._odoo_full,
                                            (self._odoo_branch or
                                             self._odoo_version),
                                            self._travis_home)
        self._addons_path = get_addons_path(self._travis_home,
                                            self._travis_build_dir,
                                            self._server_path)
        self._database = os.environ.get('MQT_TEST_DB', 'openerp_test')
        self._connection_context = context_mapping.get(
            self._odoo_version, Odoo10Context)
        self._apply_patch_odoo()
        self._get_modules_installed()

    def _check(self):
        self.wl_api._check()
        self.gh_api._check()

    def _apply_patch_odoo(self):
        """This patch is necessary because the weblate does not check which
        word and the translated are the same to use it in its percentage of
        translated"""
        paths = [os.path.join('openerp', 'tools', 'translate.py'),
                 os.path.join('odoo', 'tools', 'translate.py')]
        for path in paths:
            s_file = os.path.join(self._server_path, path)
            if not os.path.isfile(s_file):
                continue
            cmd = ["sed", "-i", "-e",
                   r"s/translation'] = src/translation'] = ''/g",
                   s_file]
            print " ".join(cmd)
            subprocess.call(cmd)

    def _get_modules_installed(self):
        self._installed_modules = []
        modules_found = []
        for name in ('__openerp__.py', '__manifest__.py'):
            modules = glob.glob('%s/**/%s' % (self._travis_build_dir, name))
            if not modules:
                continue
            modules_found.extend([
                os.path.dirname(module).split('/')[-1] for module in
                modules])
        with self._connection_context(self._server_path, self._addons_path,
                                      self._database) as odoo_context:
            odoo_context.cr.execute("select name from ir_module_module"
                                    " where state = 'installed' and "
                                    "name in %s", (tuple(modules_found),))
            modules = odoo_context.cr.dictfetchall()
            self._installed_modules = [module['name'] for module in modules]

    def _generate_odoo_po_files(self, component):
        generated = False
        with self._connection_context(self._server_path, self._addons_path,
                                      self._database) as odoo_context:
            module = component['name']
            if module not in self._installed_modules:
                return generated
            print("\n", yellow("Obtaining POT file for %s" % module))
            i18n_folder = os.path.join(self._travis_build_dir, module, 'i18n')
            if not os.path.isdir(i18n_folder):
                os.makedirs(i18n_folder)
            # Put git add for letting known git which translations to update
            po_files = glob.glob(os.path.join(i18n_folder, '*.po'))
            for lang in self._langs:
                if os.path.isfile(os.path.join(i18n_folder, lang + '.po')):
                    continue
                po_content = odoo_context.get_pot_contents(module, lang)
                if not po_content:
                    continue
                with open(os.path.join(i18n_folder, lang + '.po'), 'wb')\
                        as f_po:
                    f_po.write(po_content)
            for po_file_name in po_files:
                lang = os.path.basename(os.path.splitext(po_file_name)[0])
                if self._langs and lang not in self._langs:
                    # Limit just allowed languages if is defined
                    continue
                po_file_path = os.path.join(i18n_folder, po_file_name)
                with open(po_file_path, 'r') as f_po:
                    odoo_context.load_po(f_po, lang)
                new_content = odoo_context.get_pot_contents(module, lang)
                if not new_content:
                    continue
                with open(po_file_path, 'wb') as f_po:
                    f_po.write(new_content)
                diff = self._git.run(["diff", "HEAD", po_file_path])
                if diff.count('msgstr') == 1:
                    self._git.run(["checkout", po_file_path])
            if self._git.run(["add", "-v"] + po_files):
                generated = True
        return generated

    def _check_conflict(self, component):
        status = self._git.run(["status"])
        conflicts = [item for item in status.split('\n')
                     if (item.startswith('\tboth modified') and
                         component['filemask'].replace('/*.po', '') in item)]
        if conflicts:
            self._register_pull_request(component, status)
            return True
        return False

    def _register_pull_request(self, component, status):
        branch_name = 'conflict-%s-weblate' % self.branch
        self._git.run(["add", component['filemask']])
        self._git.run(["commit", "--no-verify",
                       "--author='Weblate bot <weblate@bot>'",
                       "-m", "[REF] i18n: Conflict on the daily cron",
                       "-m", status])
        self._git.run(["branch", "-m", branch_name])
        self._git.run(["push", "-f", "origin", branch_name])
        pull = self.gh_api.create_pull_request({
            'title': '[REF] i18n: Conflict on the daily cron',
            'head': '%s:%s' % (self.repo_name.split('/')[0].split(':')[1],
                               branch_name),
            'base': self.branch,
            'body': status
        })
        self._git.run(["checkout", "-qb", self.branch,
                       "origin/%s" % self.branch])
        self._git.run(["branch", "-D", branch_name])
        print yellow("The pull request register is: %s" % pull['html_url'])

    def _commit_weblate(self, first_commit=False):
        if ('nothing to commit, working tree clean'
                in self._git.run(["status"])):
            return first_commit
        if first_commit:
            self._git.run(["commit", "--no-verify", "--amend",
                           "--no-edit"])
        else:
            self._git.run(["commit", "--no-verify",
                           "--author='%s'" % self.GIT_COMMIT_INFO['author'],
                           "-m", self.GIT_COMMIT_INFO['message']])
            first_commit = True
        return first_commit

    def _push_git_repository(self):
        po_files = self._git.run(["show", "--format=format:'%H'",
                                  "--name-only"]).split('\n')
        if not len(po_files) > 1:
            return False
        commit = self.gh_api.create_commit(self.GIT_COMMIT_INFO['message'],
                                           self.branch,
                                           po_files[1:])
        if commit:
            for component in self.wl_api.components:
                self.wl_api.component_repository(component, 'reset')
                self.wl_api.component_repository(component, 'pull')
        return commit

    def update(self):
        self._check()
        self.wl_api.load_project(self.repo_name, self.branch)
        if not self.wl_api.components:
            print yellow("No component found for %s" % self.repo_name)
            return 1
        with self.wl_api.component_lock():
            self._git.run(["fetch", "origin"])
            first_commit = False
            for component in self.wl_api.components:
                print yellow("Component %s" % component['slug'])
                name = '%s-wl' % component['slug']
                remote = (self.wl_api.host.replace('api', 'git') + '/' +
                          self.wl_api.project['slug'] + '/' +
                          component['slug'])
                self._git.run(["checkout", "-qb", self.branch,
                               "origin/%s" % self.branch])
                self.wl_api.component_repository(component, 'pull')
                self._git.run(["remote", "add", name, remote])
                self._git.run(["fetch", name])
                if self._generate_odoo_po_files(component):
                    first_commit = self._commit_weblate(first_commit)
                self._git.run(["merge", "--squash", "-s", "recursive", "-X",
                               "ours", "%s/%s" % (name, self.branch)])
                self._git.run(["remote", "remove", name])
                if self._check_conflict(component):
                    break
                if (component['filemask'].replace('/*.po', '') in
                        self._git.run(["status"])):
                    self._git.run(["add", component['filemask']])
                    first_commit = self._commit_weblate(first_commit)
                if self._check_conflict(component):
                    break
                first_commit = self._commit_weblate(first_commit)
            if not self._push_git_repository():
                return 1
        return 0


def main(argv=None):
    try:
        TravisWeblateUpdate().update()
    except ApiException as exc:
        print yellow(str(exc))
        raise exc


if __name__ == "__main__":
    main()
