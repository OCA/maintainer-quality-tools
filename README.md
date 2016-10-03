[![Build Status](https://travis-ci.org/OCA/maintainer-quality-tools.svg)](https://travis-ci.org/OCA/maintainer-quality-tools)
[![Coverage Status](https://coveralls.io/repos/OCA/maintainer-quality-tools/badge.svg)](https://coveralls.io/r/OCA/maintainer-quality-tools)

QA Tools for Odoo maintainers
=============================

The goal is to provide helpers to ensure the quality of Odoo addons.

Sample travis configuration file (for version 7.0)
--------------------------------------------------

To setup the TravisCI continuous integration for your project, just copy the
content of the [`/sample_files`](https://github.com/OCA/maintainer-quality-tools/tree/master/sample_files)
to your project’s root directory.

If your project depends on other OCA/Github repositories, create a file called `oca_dependencies.txt` at the root of your project and list the dependencies in there, one per line:

    project_name optional_repository_url optional_branch_name

The addons path used will automatically consider these repositories.

Check your .travis file for syntax issues.
------------------------------------------

You can test your .travis file in [this linter](http://lint.travis-ci.org/) very useful when you are improving your file.

Module unit tests
-----------------

The quality tools now are also capable to test each module individually.
This is intended to check if all dependencies are correctly defined.
This is activated through the `UNIT_TEST` directive.
For current repositories to benefit this, an additional line should be added to the `env:` section,
similar to this one:

    - VERSION="8.0" UNIT_TEST="1"


Coveralls configuration file
----------------------------

Coveralls provides information on the test coverage of your modules.
Currently the Coveralls configuration is automatic, so you don't need to include a `.coveragerc`
to the repository. Please note that if you do it, it will be ignored.


Isolated pylint+flake8 checks
-----------------------------
If you want to make a build exclusive for these checks, you can add a line
on the `env:` section of the .travis.yml file with this content:

    - VERSION="7.0" LINT_CHECK="1"

You will get a faster answer about these questions and also a fast view over
semaphore icons in Travis build view.

To avoid making again these checks on other builds, you have to add
LINT_CHECK="0" variable on the line:

    - VERSION="7.0" ODOO_REPO="odoo/odoo" LINT_CHECK="0"


Disable test
------------
If you want to make a build without tests, you can add use the environment variable:
`TEST_ENABLE="0"`

You will get the databases with packages installed but without run test.
