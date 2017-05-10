FROM amsterdam/docker_python:latest
MAINTAINER datapunt.ois@amsterdam.nl

RUN apt-get update \
	&& apt-get install -y \
        libpq-dev \
        gdal-bin \
        libgeos-dev \
		postgresql-client \
		netcat \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

WORKDIR /app

COPY . /app/
COPY .jenkins/import /.jenkins-import/

RUN chown -R datapunt: /app \
    && find /app/ -name "*.pyc" -exec rm -f {} \; \
    && find /app/ -name "__pycache__" -exec rm -rf {} \; \
    && pip3 install --no-cache-dir -r requirements.txt

USER datapunt
