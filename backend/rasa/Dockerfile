FROM python:3.10

USER root

RUN apt-get update && apt-get install -y \
    libhdf5-dev \
    libhdf5-103

COPY . /app

WORKDIR /app

RUN pip install rasa==3.6.20
RUN pip install pyspellchecker==0.8.1
RUN pip install spacy==3.7.5
RUN python -m spacy download de_core_news_lg

EXPOSE 5055 5005

