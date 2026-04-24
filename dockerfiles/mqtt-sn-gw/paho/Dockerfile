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
    cmake \
    make \
    g++ \
    libssl-dev \
    wireshark \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd wireshark

RUN usermod -aG wireshark root

WORKDIR /app/paho

EXPOSE 1884

RUN git clone -b master --single-branch https://github.com/eclipse-paho/paho.mqtt-sn.embedded-c.git

RUN cd paho.mqtt-sn.embedded-c/MQTTSNGateway && ./build.sh udp

# docker build -t mqtt-sn-gw:latest .