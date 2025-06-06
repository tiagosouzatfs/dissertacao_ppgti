FROM alpine:3.22

# Necessário instalar o pacote build-base para
#    gcc	Compilador C
#    g++	Compilador C++
#    libc-dev	Headers da libc
#    make	Utilitário de compilação (Makefile)
#    binutils
RUN apk update && \
    apk add --no-cache bash && \
    apk add --no-cache git build-base

# Clonar o repositório mqtt-sn-tools
RUN git clone -b main --single-branch \
    https://github.com/njh/mqtt-sn-tools.git /mqtt-sn-tools

# Compilar o mqtt-sn-tools
WORKDIR /mqtt-sn-tools

RUN make

# Expor o diretório binários no PATH
ENV PATH="/mqtt-sn-tools/:$PATH"

# docker build -t mqtt-sn-client:latest .