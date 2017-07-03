FROM ubuntu:latest
# deze wordt gebruikt omdat er een late versie van gdal-bin gesupport wordt, deze in niet aanwezig in debian wheezy
# met python3.6

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

COPY .jenkins/import /.jenkins-import/

RUN chown -R datapunt /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

USER datapunt
