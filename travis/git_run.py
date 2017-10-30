# -*- coding: utf-8 -*-

import subprocess
from six import string_types


class GitRun(object):

    def __init__(self, repo_path, debug=False):
        self.repo_path = repo_path
        self.debug = debug

    def run(self, command):
        """Execute git command in bash
        :param list command: Git cmd to execute in self.repo_path
        :return: String output of command executed.
        """
        cmd = ['git', '--git-dir=' + self.repo_path] + command
        print(cmd if self.debug else '')
        try:
            res = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            res = None
        if isinstance(res, string_types):
            res = res.strip('\n')
        return res

    def get_items_changed(self, base_ref='HEAD'):
        """Get name of items changed in self.repo_path
        This is a wrapper method of git command:
            git diff-index --name-only --cached {base_ref}
        :param base_ref: String of branch or sha base.
            e.g. "master" or "SHA_NUMBER"
        :return: List of name of items changed
        """
        command = ['diff-index', '--name-only',
                   '--cached', base_ref]
        res = self.run(command)
        items = res.decode('UTF-8').split('\n') if res else []
        return items

    def get_branch_name(self):
        """Get branch name
        :return: String with name of current branch name"""
        command = ['rev-parse', '--abbrev-ref', 'HEAD']
        res = self.run(command)
        return res
