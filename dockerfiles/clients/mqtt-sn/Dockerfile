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

WORKDIR /app/mqtt-sn

# docker build -t mqtt-sn-client-pub-sub:latest .