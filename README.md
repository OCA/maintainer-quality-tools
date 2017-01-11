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

Test locally or on another CI
-----------------------------
You might have thouhgt "Theese tools are so cool, I want them locally", ... or on another CI.

**Here is how it goes...**

If you havn't already noticed `RUN_COMMAND_MQT`, have a look at what it does in the `test_server.py`.
We are going to use it to prepare our testbed so it's inline with the expected folder structure.

**A word on rsync:**
If you are able to cache your testbed between builds (look at your CI's cache possibilities! 
If you use docker consider dedicating it a volume!) you get huge performance gains from the 
following command `rsync -av --delete` or in its variant without translations, if you prefer, 
`rsync -av --delete --exclude 'i18n'`. Though, whatch out for tests that eventually might depend on 
some translation files!

Now define the environment variables that prepare your testbed:
In a docker-compose yaml file the relevant section could look for example like this
```yaml
   environment:
       HOME: "/home/testbed"
       TRAVIS_BUILD_DIR: "/home/testbed/build"
       RUN_COMMAND_MQT_0: "mkdir -p $TRAVIS_BUILD_DIR"  # Rsync does not create intermediate directories
       RUN_COMMAND_MQT_1: "rsync -av --delete --exclude 'i18n' /home/src/odoo-cc/* /home/testbed/odoo-9.0"
       RUN_COMMAND_MQT_2: "rsync -av --delete --exclude 'i18n' /home/src/odoo-ee /home/testbed/dependencies/"
       RUN_COMMAND_MQT_3: "rsync -av --delete --exclude 'i18n' /home/src/yourproject1/ /home/testbed/build/1_first"
       RUN_COMMAND_MQT_4: "rsync -av --delete --exclude 'i18n' /home/src/yourproject2/ /home/testbed/build/2_second"
   command:
    - travis_run_tests  # You already have mqt on your path, right?
```
What you have noticed:
 - `odoo-ee` aka enterprise addons goes into `dependencies` folder. This makes sure that its loaded before community server addons, so the web module override can work
 - Your modules that are focus of testing go into the `TRAVIS_BUILD_DIR`, look at thre `test_server.py` in order to see what's its special power.
 - If you need any special ordering (for module overrides to work), prepend it with an alfanumeric indicator such as `1_`
 - As we prepared our own testbed from scratch we simply leave out `travis_install_nightly` which normally does this job.
 - Watch out to have mqt dependencies correctly set up beforehand, look at `travis_install_nightly` and at the `.travis.yml` sample file for details.
 - No use of `ln -s`. If you work with some kind of catching it will make problems.
 
**Goody**:

If you do have your database elsewhere (on your superpower blade in your kitchen's home-datacenter)...
```
SERVER_OPTIONS: "-rUSER -wPWD --db_host=hostname_of_db_server"
PGHOST: hostname_of_db_server
PGUSER: USER
PGPASSWORD: PWD
```
What you have noticed:
 - You must set the infos twice, the `SERVER_OPTIONS` (feeding your regular odoo startup config) *and* `PG*` (feeding `createdb` command)

*Try it and let us know it is going!*
