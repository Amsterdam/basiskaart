FROM ubuntu:artful
# deze wordt gebruikt omdat er een late versie van gdal-bin gesupport wordt, deze in niet aanwezig in debian wheezy
# met python3.6

RUN apt-get update \
	&& apt-get install -y \
	build-essential \
        python3.6 \
        python3.6-dev \
        python3.6-venv \
	gcc \
	g++ \
        libpq-dev \
        gdal-bin \
	wget \
	postgresql-client \
	netcat \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt

RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.6 get-pip.py

WORKDIR /app


COPY . /app/

COPY .jenkins/import /.jenkins-import/

RUN chown -R datapunt /app

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 10

RUN pip install --upgrade pip
RUN pip install setuptools
RUN pip install -r requirements.txt

USER datapunt
