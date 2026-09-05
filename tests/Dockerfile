FROM ubuntu:26.04

WORKDIR /opt/bootstrap
COPY . /opt/bootstrap

RUN bash bootstrap.sh --check --no-packages
