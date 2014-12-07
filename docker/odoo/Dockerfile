FROM ocaimages/oca-ubuntu-base

MAINTAINER "Vauxoo"

#  Fix log odoo warning "unable to set lang fr_FR"
RUN locale-gen fr_FR \
    && locale-gen en_US.UTF-8 \
    && dpkg-reconfigure locales \
    && update-locale LANG=en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 \
    && echo 'LANG="en_US.UTF-8"' > /etc/default/locale

#  Installing postgres
RUN apt-get install --allow-unauthenticated -q postgresql-9.3 \
    postgresql-contrib-9.3 \
    postgresql-client-9.3

#  Fix shippable key issue on start postgresql - https://github.com/docker/docker/issues/783#issuecomment-56013588
RUN mkdir -p /etc/ssl/private-copy \
        && mkdir -p /etc/ssl/private \
        && mv /etc/ssl/private/* /etc/ssl/private-copy/ \
        && rm -rf /etc/ssl/private \
        && mv /etc/ssl/private-copy /etc/ssl/private \
        && chmod -R 0700 /etc/ssl/private \
        && chown -R postgres /etc/ssl/private

#  Create postgres role to root
RUN su - postgres /etc/init.d/postgresql start \
    && su - postgres -c 'psql -c "CREATE ROLE root LOGIN SUPERUSER INHERIT CREATEDB CREATEROLE;"'

RUN mkdir /extras
RUN git clone https://github.com/OCA/maintainer-quality-tools.git -b master /extras/mqt

#  Installing basic odoo dependencies
RUN WITHOUT_ODOO=1 SHIPPABLE="true" WITHOUT_DEPENDENCIES="" /extras/mqt/travis/travis_install_nightly

#  Setting global env for next shippable build
ENV WITHOUT_DEPENDENCIES 1
