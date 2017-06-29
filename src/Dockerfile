FROM amsterdam/docker_python:latest
RUN adduser --system datapunt


WORKDIR /app


COPY . /app/

COPY .jenkins/import /.jenkins-import/

RUN /app/buildgdal.sh

RUN chown -R datapunt /app
RUN pip install -r requirements.txt

USER datapunt
