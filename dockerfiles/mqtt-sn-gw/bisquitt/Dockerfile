FROM energomonitor/bisquitt:0.7.0

USER root

# Define variável para não pedir confirmação interativa
RUN export DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install ethtool net-tools iproute2 iputils-ping wireshark -y

EXPOSE 1884

# docker build -t mqtt-sn-gw-bisquitt:latest .