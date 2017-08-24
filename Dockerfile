FROM ubuntu:16.04
WORKDIR /root
COPY . maintainer-quality-tools
RUN apt-get update -yq \
    && apt-get install -yq \
        # MQT dependencies
        git \
        npm \
        python \
        ruby \
        wget \
        # Odoo dependencies
        fontconfig \
        libfreetype6 \
        libfreetype6 \
        libjpeg-turbo8 \
        liblcms2-2 \
        libldap-2.4-2 \
        libopenjpeg5 \
        libpq5 \
        libsasl2-2 \
        libtiff5 \
        libx11-6 \
        libxext6 \
        libxml2 \
        libxrender1 \
        libxslt1.1 \
        locales-all \
        phantomjs \
        tcl \
        tk \
        zlib1g \
        zlibc \
    && wget -qO- https://bootstrap.pypa.io/get-pip.py | python \
    && gem install --no-rdoc --no-ri --no-update-sources compass bootstrap-sass \
    && rm -Rf ~/.{cache,npm,gem} /var/lib/{apt/lists/*,gems/*/cache} /tmp/*
ARG VERSION=10.0
ARG ODOO_REPO=odoo/odoo
ENV ODOO_REPO=$ODOO_REPO \
    PATH=/root/maintainer-quality-tools/travis:$PATH \
    PHANTOMJS_VERSION=OS \
    TRAVIS_BUILD_DIR=/root \
    VERSION=$VERSION
RUN BUILD_DEPENDENCIES=" \
        build-essential \
        libfreetype6-dev \
        libjpeg-turbo8-dev \
        liblcms2-dev \
        libldap2-dev \
        libopenjpeg-dev \
        libpq-dev \
        libsasl2-dev \
        libtiff5-dev \
        libxml2-dev \
        libxslt1-dev \
        linux-headers-virtual \
        python-dev \
        ruby-dev \
        tcl-dev \
        tk-dev" \
    && apt-get update -yq \
    && apt-get install -yq $BUILD_DEPENDENCIES \
    && travis_install_nightly \
    && apt-get -yq purge $BUILD_DEPENDENCIES \
    && apt-get -yq autoremove --purge \
    && rm -Rf ~/.{cache,npm,gem} /var/lib/{apt/lists/*,gems/*/cache} /tmp/*
CMD ["travis_run_tests"]
