FROM python:3.8

COPY ./code /code

WORKDIR /code

RUN pip install -r requirements.txt