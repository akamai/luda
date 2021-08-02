FROM python:3.8-slim-buster

WORKDIR /code
RUN yes | apt-get update
RUN yes | apt install build-essential
RUN yes | apt-get install manpages-dev
RUN yes | pip3 install Cython
RUN pip3 install notebook
RUN mkdir -p /usr/share/man/man1
RUN yes | apt-get install default-jdk
RUN yes | apt-get install vim
RUN yes | apt-get install screen
RUN apt-get install htop


COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "/bin/bash" ]
