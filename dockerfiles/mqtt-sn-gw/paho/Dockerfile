FROM alpine:3.22.0

RUN apk update && \
    apk add --no-cache bash git make build-base && \
    apk add --no-cache cmake g++ gcc musl-dev openssl openssl-dev ethtool net-tools

RUN git clone -b master --single-branch \
    https://github.com/eclipse-paho/paho.mqtt-sn.embedded-c.git /mqtt-sn-gw

# Compilar o mqtt-sn-gw
WORKDIR /mqtt-sn-gw

# docker build -t mqtt-sn-gw:latest .