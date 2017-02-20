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
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

COPY . /app/
COPY requirements.txt /app/
COPY .jenkins-import /.jenkins-import/

WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

RUN chown -R datapunt /app
USER datapunt
