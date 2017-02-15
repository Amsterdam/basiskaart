FROM amsterdam/docker_python:latest
MAINTAINER datapunt.ois@amsterdam.nl

RUN apt-get update \
	&& apt-get install -y \
		gdal-bin postgresql-client \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

COPY basiskaart /app/
COPY .jenkins-import /.jenkins-import/
COPY requirements.txt /app/

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

RUN chown -R datapunt /app
USER datapunt