#!/usr/bin/env python

import os
import subprocess

import getaddons


repo_dir = os.environ.get("TRAVIS_BUILD_DIR", ".")
addons_path = os.path.join(repo_dir, 'tests', 'test_repo')
addons_path_with_subfolders = os.path.join(
    repo_dir, "tests", "test_repo_with_subfolders")
exclude = os.environ.get("EXCLUDE")
# Testing getaddons
assert getaddons.main() == 1
getaddons.main(["getaddons.py", addons_path])
getaddons.main(["getaddons.py", "-m", addons_path])
getaddons.main(["getaddons.py", "-m",
                addons_path + "/" if addons_path[-1] == '/' else addons_path])
if exclude:
    getaddons.main(["getaddons.py", "-m", addons_path, "-e", exclude])
    getaddons.main(["getaddons.py", "-e", exclude, addons_path])

# Testing addons-path order is alfanumerical
addon_paths_alfanumerical_order_is = getaddons.get_addons(
    addons_path_with_subfolders)
addon_paths_alfanumerical_order_should = [
    '1_testfolder',
    '2_testfolder',
]
combined = []
for i, item in enumerate(addon_paths_alfanumerical_order_should):
    combined.append([addon_paths_alfanumerical_order_is[i], item])
print combined.__repr__()
assert len(combined) == len(addon_paths_alfanumerical_order_is)
for ist, should in combined:
    assert ist.rstrip('/').rstrip('\\').endswith(should)


# Testing git run from getaddons
getaddons.get_modules_changed(repo_dir)


# Testing empty paths and pylint_run fix of:
# https://www.mail-archive.com/code-quality@python.org/msg00294.html
if os.environ.get('LINT_CHECK', 0) == '1':
    import run_pylint
    pylint_rcfile = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'cfg',
        "travis_run_pylint.cfg")
    count_errors = run_pylint.main([
        "--config-file=" + pylint_rcfile,
        "--extra-params", "-d", "--extra-params", "all",
        "--extra-params", "-e", "--extra-params", "F0010,duplicate-key",
        "--path", repo_dir], standalone_mode=False)
    assert 2 == count_errors

    empty_path = os.path.join(repo_dir, 'empty_path')
    if not os.path.exists(empty_path):
        os.mkdir(empty_path)
    count_errors = run_pylint.main([
        "--config-file=" + pylint_rcfile,
        "--path", empty_path], standalone_mode=False)
    assert -1 == count_errors

    if os.environ.get('TRAVIS_PULL_REQUEST', 'false') != 'false':
        git_script_path = os.path.join(os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))), 'git')
        pre_commit_returned = subprocess.call(os.path.join(
            git_script_path, 'pre-commit'))
        assert pre_commit_returned == 0, \
            "Git pre-commit script returned value != 0"
