FROM build.datapunt.amsterdam.nl:5000/atlas/python:latest
MAINTAINER datapunt.ois@amsterdam.nl

COPY apt/*.list /etc/apt/sources.list.d/

RUN apt-get update \
	&& apt-get install -y \
	    gdal-bin/testing \
		libgeos-dev \
		postgresql-client \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

COPY . /app/
COPY requirements.txt /app/
COPY .jenkins-import /.jenkins-import/

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R datapunt /app
USER datapunt