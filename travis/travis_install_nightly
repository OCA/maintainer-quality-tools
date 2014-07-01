#!/bin/sh

VERSION=$1
# Install the nightly version of OpenERP
sudo apt-get install -qq graphviz # needed?
pip install QUnitSuite # web unit tests fail without this
wget http://nightly.openerp.com/7.0/nightly/deb/openerp_${VERSION}-latest-1_all.deb
sudo dpkg -i openerp_${VERSION}-latest-1_all.deb || sudo apt-get -f install

