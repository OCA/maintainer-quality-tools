# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import subprocess
import sys


def apply_patches(fname_patch, odoo_path, dependencies_path):
    """Read a patch file to apply them.
    :param fname_patch: Path of the file with list of patches
                        The format to use is:
                        odoo url.patch
                        extra_addons/other-repo url.patch
    :param odoo_path: Path of folder where odoo was cloned.
    :param dependencies_path: Base path where dependencies was cloned.
    """
    if not os.path.isfile(fname_patch):
        return
    print("Applying patch '%s'" % fname_patch)
    with open(fname_patch) as fp:
        for line in fp:
            if not line:
                continue
            repo, patch_url = line.strip(' \n').split(' ', 1)
            if repo == 'odoo':
                repo = odoo_path
            if repo.startswith('extra_addons'):
                repo = repo.replace('extra_addons', dependencies_path, 1)
            git_cmd = [
                'git', '--git-dir=%s' % os.path.join(repo, '.git'),
                '--work-tree=%s' % repo, '-c', 'user.name="MQT Patches"',
                '-c', 'user.email="mqt@patches"',
                '-c', 'commit.gpgsign=false',
            ]
            p_wget = ['wget', '-O-', patch_url]
            if 'api.github.com' in patch_url:
                github_token = os.environ.get('GITHUB_TOKEN')
                p_wget += [
                    '--header=Authorization: token %s' % github_token,
                    '--header=Accept: application/vnd.github.VERSION.patch',
                ]
            p_wget = subprocess.Popen(
                p_wget, stdout=subprocess.PIPE)
            p_git = subprocess.Popen(
                git_cmd + ['am', '--signoff'],
                stdin=p_wget.stdout, stdout=subprocess.PIPE)
            p_wget.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            p_git.communicate()[0]


if __name__ == '__main__':
    fname_patch = sys.argv[1]
    odoo_path = sys.argv[2]
    dependencies_path = sys.argv[3]
    apply_patches(fname_patch, odoo_path, dependencies_path)
