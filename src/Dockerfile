FROM amsterdam/docker_python:latest

#RUN add-apt-repository ppa:ubuntugis/ppa




WORKDIR /app


COPY . /app/
COPY .jenkins/import /.jenkins-import/

RUN /app/buildgdal.sh

RUN chown -R datapunt: /app \
    && pip3 install --no-cache-dir -r requirements.txt

USER datapunt
