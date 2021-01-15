[![Build Status](https://travis-ci.org/OCA/maintainer-quality-tools.svg)](https://travis-ci.org/OCA/maintainer-quality-tools)
[![codecov](https://codecov.io/gh/OCA/maintainer-quality-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/OCA/maintainer-quality-tools)

QA Tools for Odoo maintainers (MQT)
===================================

The goal of Maintainer Quality Tools (MQT) is to provide helpers to ensure the quality of Odoo addons.

Sample travis configuration files
---------------------------------

To configure a repository to use Travis CI with these tools, the easiest is
to start from the `copier` template in https://github.com/OCA/oca-addons-repo-template.

Dependencies on other OCA repositories
--------------------------------------

If your project depends on other OCA or other Github repositories, create a file called `oca_dependencies.txt` at the root of your project and list the dependencies there. One per line like so:

    project_name optional_repository_url optional_branch_name

During testbed setup, MQT will automatically download and place these repositories accordingly into the addon path.
Note on addons path ordering: They will be placed after your own repo, but before the odoo core repo.

TODO: document MQT_DEP=PIP mode

Check your .travis file for syntax issues
-----------------------------------------

You can test your .travis file in [this linter](http://lint.travis-ci.org/).
This is very useful when you are improving your file.

Multiple values for environment variable VERSION
------------------------------------------------

You can use branch or pull request into environment variable VERSION:

- Branch 10.0
```
    VERSION="10.0" ODOO_REPO="odoo/odoo"
```

- Pull request odoo/odoo#143
```
    VERSION="pull/143" ODOO_REPO="odoo/odoo"
```

Using custom branch inside odoo repository using ODOO_BRANCH
------------------------------------------------------------

You can use the custom branch into the ODOO_REPO using the environment variable ODOO_BRANCH:


- Branch saas-17
```
  ODOO_REPO="odoo/odoo" ODOO_BRANCH="saas-17"
```

Module unit tests
-----------------

MQT is also capable to test each module individually.
The intention is to check if all dependencies are correctly defined.
Activate it through the `UNIT_TEST` directive.
An additional line should be added to the `env:` section,
similar to this one:

    - VERSION="8.0" UNIT_TEST="1"


Codecov configuration file
--------------------------

[Codecov](https://codecov.io/) provides information on the test coverage of your modules.
The configurations is automatic (check default configuration [here](cfg/.coveragerc)).
So you don't need to include a `.coveragerc` into the repository,
If you do it, it will be simply ignored.

**NOTE:** the current configuration automatically ignores `*_example` modules
from coverage check.
See [maintainer-tools CONTRIBUTING doc](https://github.com/OCA/maintainer-tools/blob/master/CONTRIBUTING.md#tests) for further info on tests.

Names used for the test databases
---------------------------------

MQT has a nice feature of organizing your testing databases.
You might want to do that if you want to double them up as
staging DBs or if you want to work with an advanced set of
templates in order to speed up your CI pipeline.
Just specify at will:
`MQT_TEMPLATE_DB='mqt_odoo_template' MQT_TEST_DB='mqt_odoo_test'`.
Give us feedback on you experiences, and if you could share findings
from your use case, there might be some grateful people arround.


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
If you want to make a build without tests, you can use the following directive:
`TEST_ENABLE="0"`

You will simply get the databases with packages installed,
but whithout running any tests.
