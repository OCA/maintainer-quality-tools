FROM ubuntu:14.04

MAINTAINER "Vauxoo"

#  Fix http://stackoverflow.com/questions/22466255/is-it-possibe-to-answer-dialog-questions-when-installing-under-docker
ENV DEBIAN_FRONTEND noninteractive

#  Setting utf-8 to python enconding
ENV PYTHONIOENCODING utf-8

#  Basic configuration for a CI image
RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf \
    && echo 'APT::Get::force-yes "true";' >> /etc/apt/apt.conf

#  Installing basic OS package and dev packages
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
    libssl-dev \
    libyaml-dev \
    libjpeg-dev \
    libgeoip-dev \
    libffi-dev \
    libqrencode-dev \
    libfreetype6-dev \
    zlib1g-dev \
    libpq-dev \
    python-pip

#  Add git config data to root user. (Required to use git command)
RUN git config --global user.name oca_docker \
    && git config --global user.email hello@oca.com

#  Fix http://www.nigeldunn.com/2011/05/14/ubuntu-11-04-libjpeg-so-libpng-so-php-installation-issues/
RUN ln -s /usr/include/freetype2 /usr/local/include/freetype \
    && ln -s /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/ \
    && ln -s /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/ \
    && ln -s /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
