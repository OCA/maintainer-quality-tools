#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from getpass import getuser
from git_run import GitRun


def translate_gitlab_env():
    """ This sets Travis CI's variables using GitLab CI's variables. This
        makes possible to run scripts which depend on Travis CI's variables
        when running under Gitlab CI.

         For documentation on these environment variables, please check:
        - Predefined environment variables on Travis CI:
          https://docs.travis-ci.com/user/environment-variables#Default-Environment-Variables
        - Predefined environment variables on GitLab CI:
          https://docs.gitlab.com/ee/ci/variables/#predefined-variables-environment-variables
    """
    if not os.environ.get("GITLAB_CI"):
        return False
    build_dir = os.environ.get("CI_PROJECT_DIR", ".")
    git_run_obj = GitRun(repo_path=os.path.join(build_dir, ".git"))
    commit_message = git_run_obj.run(["log", "-1", "--pretty=%b"])
    head_branch = os.environ.get("CI_COMMIT_REF_NAME")
    # This is a guess
    target_branch = os.environ.get("VERSION")

    # Set environment variables
    os.environ.update({
        # Predefined values
        "TRAVIS": "true",
        "CONTINUOUS_INTEGRATION": "true",
        "HAS_JOSH_K_SEAL_OF_APPROVAL": "true",
        "RAILS_ENV": "test",
        "RACK_ENV": "test",
        "MERB_ENV": "test",
        "TRAVIS_ALLOW_FAILURE": "false",
        "TRAVIS_JOB_NUMBER": "1",
        "TRAVIS_TEST_RESULT": "0",
        "TRAVIS_COMMIT_RANGE": "unknown",
        # Dinamic values
        "TRAVIS_BRANCH": target_branch,
        "TRAVIS_COMMIT_MESSAGE": commit_message,
        "TRAVIS_OS_NAME": sys.platform,
        "TRAVIS_SUDO": "true" if getuser() == "root" else "false",
    })

# Set variables whose values are already directly set in other variables
    equivalent_vars = [
        ("TRAVIS_BUILD_DIR", "CI_PROJECT_DIR"),
        ("TRAVIS_BUILD_ID", "CI_BUILD_ID"),
        ("TRAVIS_BUILD_NUMBER", "CI_JOB_ID"),
        ("TRAVIS_COMMIT", "CI_COMMIT_SHA"),
        ("TRAVIS_EVENT_TYPE", "CI_PIPELINE_SOURCE"),
        ("TRAVIS_JOB_ID", "CI_JOB_ID"),
        ("TRAVIS_REPO_SLUG", "CI_PROJECT_PATH"),
        ("TRAVIS_BUILD_STAGE_NAME", "CI_BUILD_STAGE"),
    ]
    os.environ.update({
        travis_var: os.environ.get(gitlab_var)
        for travis_var, gitlab_var in equivalent_vars
        if gitlab_var in os.environ
    })

    # If within an MR
    is_mr = target_branch != head_branch
    if is_mr:
        os.environ.update({
            # there's no way to know the MR number. For more info, see:
            # https://gitlab.com/gitlab-org/gitlab-ce/issues/15280
            "TRAVIS_PULL_REQUEST": "unknown",
            "TRAVIS_PULL_REQUEST_BRANCH": head_branch,
            "TRAVIS_PULL_REQUEST_SHA": os.environ.get("CI_COMMIT_SHA"),
            "TRAVIS_PULL_REQUEST_SLUG": os.environ.get("CI_PROJECT_PATH"),
        })
    else:
        os.environ.update({
            "TRAVIS_PULL_REQUEST": "false",
            "TRAVIS_PULL_REQUEST_BRANCH": "",
            "TRAVIS_PULL_REQUEST_SHA": "",
            "TRAVIS_PULL_REQUEST_SLUG": "",
        })
    return True
