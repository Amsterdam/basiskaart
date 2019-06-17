FROM ubuntu:latest
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

RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py
RUN python3.6 get-pip.py

WORKDIR /app

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 10

# CI hook - see .jenkins/README.TXT
COPY .jenkins/import /.jenkins-import/

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

RUN chown -R datapunt /app

USER datapunt
