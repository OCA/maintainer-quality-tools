Script for making the same tests as in Travis before committing
===============================================================

This script allows to make a test before each commit you make on your local
git repository, checking same things as in Travis LINT_CHECK phase of
OCA maintainer quality tools.

For using it, you can choose from two options:

1. Create symbolic link of files to local git repository into .git/hooks, and you will enable the
   checks for that git repository.

   ```bash
   git clone git@github.com:OCA/maintainer-quality-tools.git ${HOME}/lint-hook
   ln -sf ${HOME}/lint-hook/git/* {YOUR_PROJECT}/.git/hooks/.
   ```

2. Create symbolic link of files to git template directory.

  In Ubuntu, it's located in:

     /usr/share/git-core/templates/hooks/


  In OS X, it's located in:

    Installed from MAC-port

        /opt/local/share/git-core/templates/hooks/


Then, making `git init` inside a git repository, these files will be copied,
and you will have these checks available for it.

   ```bash
   git clone git@github.com:OCA/maintainer-quality-tools.git ${HOME}/lint-hook
   sudo ln -sf ${HOME}/lint-hook/git/* /usr/share/git-core/templates/hooks/.
   cd {YOUR_PROJECT}
   git init .
   ```

**IMPORTANT** Don't forget to install/update flake8, pep8 and pylint-odoo modules to
have the same checks as Travis. Don't use distribution packages, as they are 
outdated. Use pip ones:

```bash
# pip install --upgrade flake8 pep8
$ git clone https://github.com/OCA/pylint-odoo
$ cd pylint-odoo
# ./install.sh
```

You can bypass these checks setting environment variable NOLINT before calling
commit, e.g, `NOLINT=1 git commit`.

You can force use a lint configuration setting environment variable VERSION with
the number of version of odoo before calling
commit, e.g, `VERSION=7.0 git commit`
If VERSION is not assigned then will use current branch name starts with "{VERSION}(-|_).*". e.g. `7.0-my-branch` or `7.0_my_branch`
