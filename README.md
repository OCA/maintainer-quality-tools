[![Build Status](https://travis-ci.org/OCA/maintainer-quality-tools.svg)](https://travis-ci.org/OCA/maintainer-quality-tools)

QA Tools for Odoo maintainers
=============================

The goal is to provide helpers to ensure the quality of Odoo addons.

Sample travis configuration file (for version 7.0)
--------------------------------------------------

To setup the TravisCI continuous integration for your project, just copy the
content of the [`/sample_files`](https://github.com/OCA/maintainer-quality-tools/tree/master/sample_files)
to your project’s root directory.

If your project depends on other OCA/Github repositories simply add the following under `before_install` section:

    install:
      - git clone https://github.com/OCA/a_project_x ${HOME}/a_project_x -b ${VERSION}
      - git clone https://github.com/OCA/a_project_y ${HOME}/a_project_y -b ${VERSION}

The addons path used will automatically consider these repositories.


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
Currently the Coveralls configuration is automatic, so you don’t need to include a `.covaragerc`
to the repository. Pelase note that if you do, it will be ignored.
