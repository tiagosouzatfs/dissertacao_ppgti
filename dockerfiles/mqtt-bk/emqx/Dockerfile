FROM emqx/emqx:5.8.6

USER root

# Define variável para não pedir confirmação interativa
RUN export DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install ethtool net-tools iproute2 iputils-ping wireshark -y

USER emqx

EXPOSE 1884

# docker build -t mqtt-bk-emqx:latest .