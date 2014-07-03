QA Tools for Odoo maintainers
=============================

The goal is to provide helpers to ensure the quality of Odoo addons. 

Sample travis configuration file
---------------------------------

Put this in your project's `.travis.yml`:

    language: python
    python:
      - "2.7"
    
    virtualenv:
      system_site_packages: true
    
    install:
     - git clone https://github.com/gurneyalex/maintainer-quality-tools.git $HOME/maintainer-quality-tools
     - export PATH=$HOME/maintainer-quality-tools/travis:$PATH
     - $HOME/maintainer-quality-tools/travis/travis_install_nightly 7.0
     - pip install coveralls flake8
    
    services:
      - postgresql
    
    script:
        - travis_run_flake8
        - travis_run_tests 7.0 openerp_test
    
    after_success:
      coveralls

If your project depends on other OCA/Github repositories simply add the following under `before_install` section:

    before_install:
      - git clone https://github.com/OCA/a_project_x $HOME/a_project_x -b 7.0
      - git clone https://github.com/OCA/a_project_y $HOME/a_project_y -b 7.0
      
And add path to the cloned repositories to the `travis_run_tests` command:

    script:
      - travis_run_tests 7.0 openerp_test $HOME/a_project_x $HOME/a_project_y
