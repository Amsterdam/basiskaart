FROM amsterdam/python:3.9-buster

RUN apt-get update \
	&& apt-get install -y gdal-bin \
	&& adduser --system datapunt

WORKDIR /app

# CI hook - see .jenkins/README.TXT
COPY .jenkins/import /.jenkins-import/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chown -R datapunt /app

USER datapunt
