#!/bin/sh

VERSION=$1
# Install the nightly version of OpenERP
wget http://nightly.openerp.com/7.0/nightly/deb/openerp_${VERSION}-latest-1_all.deb
dpkg -i openerp_${VERSION}-latest-1_all.deb


