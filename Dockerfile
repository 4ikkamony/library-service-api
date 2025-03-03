FROM python:3.12-alpine

WORKDIR /usr/src/app

COPY requirements.txt requirements.txt

RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apk update && apk add --no-cache dos2unix

RUN dos2unix /usr/src/app/commands/*.sh

RUN adduser --disabled-password --no-create-home django-user

RUN chmod -R +x /usr/src/app/commands/ \
    && chmod -R 777 /usr/src/app

USER django-user
