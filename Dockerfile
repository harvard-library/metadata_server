FROM ubuntu:latest as builder
MAINTAINER Chip Goines <chip_goines@harvard.edu>
# Borrowed Heavily from Default Docker File for Loris.

# Initialize Ubuntu environment with required packages.
ARG APP_VERSION='v1.6.45'
ARG APP_LOCATION='https://github.com/harvard-library/metadata_server.git'

ENV APP_NAME="metadata_server"
ENV APP_ID_NUMBER=54422
ENV APP_ID_NAME=ids

ENV APP_VERSION_LOC=${APP_VERSION}
ENV APP_LOCATION_LOC=${APP_LOCATION}

RUN DEBIAN_FRONTEND=non-interactive && \
    apt-get update -y && \
    apt-get install -y curl git && \
    groupadd -g ${APP_ID_NUMBER} ${APP_ID_NAME} && \
    useradd -u ${APP_ID_NUMBER} -g www-data -m -d /home/${APP_ID_NAME} -s /sbin/false ${APP_ID_NAME} && \
    cd /home/${APP_ID_NAME} && \
    git clone -b ${APP_VERSION_LOC} ${APP_LOCATION_LOC} && \
    mkdir -p /home/${APP_ID_NAME}/tmp && \
    chown -R ${APP_ID_NAME}:www-data /home/${APP_ID_NAME} && \
    chmod -R g+w /home/${APP_ID_NAME} && \
    touch /home/${APP_ID_NAME}/${APP_NAME}/.env && \
    mkdir /home/app && \
    mv /home/${APP_ID_NAME}/${APP_NAME} /home/app/appbuild && \
    sed -i '/uWSGI/c\uwsgi' /home/app/appbuild/requirements.txt && \
    curl -o /home/app/appbuild/global-bundle.pem https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem

FROM artifactory.huit.harvard.edu/lts/apache_base:1.0.0

ENV APP_NAME="metadata_server"
ENV APP_ID_NUMBER=54422
ENV APP_ID_NAME=ids
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

COPY requirements.txt /root/requirements.txt

RUN cd /root && \
    apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y libffi-dev locales libcap2-bin apache2 libapache2-mod-wsgi-py3 curl pkg-config cmake unzip libxml2-dev libxslt1-dev python3 python3-pip build-essential supervisor ca-certificates && \
    pip3 install pip-tools && \
    apt-get clean && \
    a2enmod rewrite && \
    groupadd -g ${APP_ID_NUMBER} ${APP_ID_NAME} && \
    useradd -u ${APP_ID_NUMBER} -g www-data -m -d /home/${APP_ID_NAME} -s /sbin/false ${APP_ID_NAME} && \
    chown -R ${APP_ID_NAME}:www-data /var/log/supervisor && \
    mkdir /var/tmp/${APP_ID_NAME} && \
    chown ${APP_ID_NAME}:www-data /var/tmp/${APP_ID_NAME} && \
    chown ${APP_ID_NAME}:www-data /var/run/supervisor && \
    chown -R ${APP_ID_NAME}:www-data /var/log/apache2 && \
    chown -R ${APP_ID_NAME}:www-data /var/run/apache2

COPY supervisor /etc/supervisor/
# LIMITATION IN DOCKER FILE
COPY --from=builder --chown=ids:www-data /home/app/appbuild /home/ids/appbuild
RUN mv /home/ids/appbuild /home/ids/${APP_NAME} && \
    cd /home/ids/${APP_NAME} && pip3 install -r /root/requirements.txt && \
    apt-get remove -y gcc && \
    sed -i 's/USER=www-data/USER=${APP_ID_NAME}/' /etc/apache2/envvars

WORKDIR /home/${APP_ID_NAME}/${APP_NAME}

EXPOSE 8080
EXPOSE 8443
USER ids
CMD ["/usr/bin/supervisord"]
