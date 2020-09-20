FROM python:3.6-slim

RUN apt-get update &&\
    apt-get install -y git &&\
    rm -rf /var/lib/apt/lists/*

RUN useradd dummy

WORKDIR /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn
COPY app.py /app
ADD application /app/application

USER dummy
