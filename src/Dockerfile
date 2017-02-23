FROM ubuntu:xenial
MAINTAINER datapunt.ois@amsterdam.nl

RUN apt-get update \
	&& apt-get install -y \
        python3 \
        python3-dev \
        python3-pip \
        libpq-dev \
        gdal-bin \
		postgresql-client \
		netcat \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

WORKDIR /app

COPY . /app/
COPY . .jenkins/import /.jenkins-import/

RUN pip3 install --no-cache-dir -r requirements.txt
USER datapunt
