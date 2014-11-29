#!/usr/bin/env python

import argparse
import os
import subprocess


def run_output(l, cwd=None):
    print "run output:", ' '.join( l ), "into", cwd
    return subprocess.Popen(l, stdout=subprocess.PIPE, cwd=cwd).communicate()[0]


def is_git_repo(path):
    if os.path.isdir(os.path.join(path, 'refs')):
        return True
    return False


def run_git_cmd(cmd, git_dir=None, path=None):
    cmd_git = ["git"]
    if git_dir:
        if is_git_repo(git_dir):
            real_git_dir = git_dir
        elif is_git_repo(os.path.join(git_dir, '.git')):
            real_git_dir = os.path.join(git_dir, '.git')
        cmd_git.append("--git-dir=" + real_git_dir)
    cmd_git.extend(cmd)
    res = run_output(cmd_git, cwd=path)
    return res


def git_init_repo(path):
    res = False
    if not os.path.isdir(path):
        os.mkdir(path)
    if not is_git_repo(path):
        res = run_git_cmd(["init", path])
    return res


def git_reset_remote(repo, remote_name, path):
    git_init_repo(path)
    run_git_cmd(["remote", "remove", remote_name], path)
    res = run_git_cmd(["remote", "add", remote_name, repo], path)
    return res


def git_clone_update(repo, branch, path=None):
    if not path:
        path = os.getcwd()
    remote_name = 'origin'
    git_reset_remote(repo, remote_name, path)
    run_git_cmd(["fetch", remote_name], path)
    run_git_cmd(["checkout", "-f", branch], path=path)
    run_git_cmd(["reset", "--hard", branch], path=path)


def main():
    parser = argparse.ArgumentParser(
        description="Script to download locally"
                    " a git repository"
                    " or if exists update it.")
    parser.add_argument("repo_url",
                       help="url of repository"
                             " source of clone.")
    parser.add_argument("path",
                        help="Local path to save"
                             " tree files cloned.",
                        default='.')
    parser.add_argument("-b", dest="branch",
                        help="The name of the branch"
                             "source of clone.")
    args = parser.parse_args()
    git_clone_update(
        args.repo_url,
        args.branch,
        path=args.path)



if __name__ == '__main__':
    main()
