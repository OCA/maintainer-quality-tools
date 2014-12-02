FROM ubuntu:14.04

MAINTAINER "Moises Lopez <moylop260@vauxoo.com>"

RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf \
    && echo 'APT::Get::force-yes "true";' >> /etc/apt/apt.conf
RUN locale-gen fr_FR \
    && locale-gen en_US.UTF-8 \
    && dpkg-reconfigure locales \
    && update-locale LANG=en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 \
    && echo 'LANG="en_US.UTF-8"' > /etc/default/locale

ENV PYTHONIOENCODING utf-8

RUN apt-get update -q && apt-get upgrade -q \
    && apt-get install --allow-unauthenticated -q bzr \
    python \
    python-dev \
    python-setuptools \
    git \
    vim \
    nano \
    wget \
    tmux \
    htop \
    postgresql-9.3 \
    postgresql-contrib-9.3

# Installing pip
RUN cd /tmp && wget -q https://raw.githubusercontent.com/pypa/pip/master/contrib/get-pip.py && python get-pip.py

# Add git config data to root user
RUN git config --global user.name oca_docker \
    && git config --global user.email hello@oca.com

# Fix shippable key issue on start postgresql - https://github.com/docker/docker/issues/783#issuecomment-56013588
RUN sudo mkdir -p /etc/ssl/private-copy \
        && sudo mkdir -p /etc/ssl/private \
        && sudo mv /etc/ssl/private/* /etc/ssl/private-copy/ \
        && sudo rm -rf /etc/ssl/private \
        && sudo mv /etc/ssl/private-copy /etc/ssl/private \
        && sudo chmod -R 0700 /etc/ssl/private \
        && sudo chown -R postgres /etc/ssl/private

# Change to user postgres
USER postgres

# Create postgres role to root
RUN /etc/init.d/postgresql start \
    && psql -c  "CREATE ROLE root LOGIN SUPERUSER INHERIT CREATEDB CREATEROLE;"

USER root
WORKDIR /root

# Workaround to force using system site packages (see https://github.com/Shippable/support/issues/241#issuecomment-57947925)
RUN rm -rf $VIRTUAL_ENV/lib/python2.7/no-global-site-packages.txt

ADD * /tmp/
RUN WITHOUT_ODOO=1 /tmp/travis_install_nightly
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*
