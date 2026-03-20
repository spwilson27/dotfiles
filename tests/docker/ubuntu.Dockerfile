FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y python3 python3-pytest python3-pexpect ca-certificates sudo gnupg2 \
    && rm -rf /var/lib/apt/lists/*
