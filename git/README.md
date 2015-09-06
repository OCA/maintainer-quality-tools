Script for making the same tests as in Travis before committing
===============================================================

This script allows to make a test before each commit you make on your local
git repository, checking same things as in Travis LINT_CHECK phase of
OCA maintainer quality tools.

For using it, you can choose from two options:

1. Copy files to local git repository into .git/hooks, and you will enable the
   checks for that git repository.

2. Copy files to git template directory. In Ubuntu, it's located in:

   /usr/share/git-core/templates/hooks/

Then, making `git init` inside a git repository, these files will be copied,
and you will have these checks available for it.

**IMPORTANT** Don't forget to install/update flake8, pep8 and oca-pylint-plugin modules to
have the same checks as Travis. Don't use distribution packages, as they are 
outdated. Use pip ones:
`# pip install --upgrade flake8 pep8 oca-pylint-plugin`

You can bypass these checks setting environment variable NOLINT before calling
commit, e.g, `NOLINT=1 git commit`.

You can use a lint configuration setting environment variable VERSION with
the number of version of odoo before calling
commit, e.g, `VERSION=7.0 git commit`.
