QA Tools for Odoo maintainers
=============================

The goal is to provide helpers to ensure the quality of Odoo addons. 

Sample travis configuration file (for version 7.0)
--------------------------------------------------

To setup the TravisCI continuous integration for your project, just copy the
content of the `/sample_files` to your project’s root directory.

If your project depends on other OCA/Github repositories simply add the following under `before_install` section:

    install:
      - git clone https://github.com/OCA/a_project_x $HOME/a_project_x -b 7.0
      - git clone https://github.com/OCA/a_project_y $HOME/a_project_y -b 7.0

And add path to the cloned repositories to the `travis_run_tests` command:

    script:
      - travis_run_tests 7.0 $HOME/a_project_x $HOME/a_project_y

Sample coveralls configuration file
------------------------------------

You can use the following sample (also available in the travis directory) to
configure the reporting by coveralls.io. Copy it to `.coveragerc` in the root
of your project, and change the include value to match the name of your
project:

    [report]
    include =
        */OCA/<YOUR_PROJECT_NAME_HERE>/*

    omit =
        */tests/*
        *__init__.py

    # Regexes for lines to exclude from consideration
    exclude_lines =
        # Have to re-enable the standard pragma
        pragma: no cover

        # Don't complain about null context checking
        if context is None:
