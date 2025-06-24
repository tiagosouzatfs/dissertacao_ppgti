#FROM alpine:3.22.0

#RUN apk update && \
#    apk add --no-cache bash git make build-base ethtool net-tools

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    vim \
    git \
    build-essential \
    ethtool \
    iproute2 \
    net-tools && \
    rm -rf /var/lib/apt/lists/*

# Clonar o repositório mqtt-sn-tools
RUN git clone -b main --single-branch \
    https://github.com/njh/mqtt-sn-tools.git /mqtt-sn-tools

# Compilar o mqtt-sn-tools
WORKDIR /mqtt-sn-tools

RUN make

# Expor o diretório binários no PATH
ENV PATH="/mqtt-sn-tools/:$PATH"

# docker build -t mqtt-sn-client:latest .