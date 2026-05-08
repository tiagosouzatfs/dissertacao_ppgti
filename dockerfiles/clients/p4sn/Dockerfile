FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    vim \
    git \
    build-essential \
    ethtool \
    iproute2 \
    net-tools \
    wireshark \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd wireshark

RUN usermod -aG wireshark root

WORKDIR /app/p4ssn

# docker build -t p4sn-client-pub-sub:latest .