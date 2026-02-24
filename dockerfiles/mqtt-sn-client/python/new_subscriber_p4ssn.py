#!/usr/bin/env python3

import socket
import struct
import random
import time
import sys

# =============================================================================
# 1. Constantes do protocolo
# =============================================================================

MQTTSN_CONNECT = 0x04
MQTTSN_CONNACK = 0x05
MQTTSN_SUBSCRIBE = 0x12
MQTTSN_SUBACK = 0x13
MQTTSN_UNSUBSCRIBE = 0x14
MQTTSN_UNSUBACK = 0x15
MQTTSN_PUBLISH = 0x0C
MQTTSN_DISCONNECT = 0x18
MQTTSN_PINGREQ = 0x16
MQTTSN_PINGRESP = 0x17
MQTTSN_PUBACK = 0x0D
MQTTSN_PUBREC = 0x0F
MQTTSN_PUBREL = 0x10
MQTTSN_PUBCOMP = 0x0E

QOS_0 = 0b00
QOS_1 = 0b01
QOS_2 = 0b10

TOPICIDTYPE_TOPICNAME = 0b00
TOPICIDTYPE_PREDEFINED = 0b01
TOPICIDTYPE_SHORT = 0b10

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

GW_IP = "10.0.0.1"
GW_PORT = 1884
CLIENT_IP = "10.0.0.3"

# =============================================================================
# 2. Funções auxiliares
# =============================================================================

def xor_data(data_bytes, mask_int):
    mask_bytes = mask_int.to_bytes(64, "big")
    return bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])

# =============================================================================
# 3. Funções MQTT-SN básicas
# =============================================================================

def build_connect(client_id=None, duration=30):
    flags = 0x04
    protocol_id = 0x01
    if client_id is None:
        client_id = f"sub_client_{random.randint(1000,9999)}".encode()
    payload = struct.pack(">BBH", flags, protocol_id, duration) + client_id
    length = len(payload) + 2
    return struct.pack(">BB", length, MQTTSN_CONNECT) + payload


def build_subscribe(topic_input, msg_id, qos_level, topic_type):

    flags = (qos_level << 5) | topic_type

    if topic_type == TOPICIDTYPE_TOPICNAME:
        payload = struct.pack(">BH", flags, msg_id) + topic_input.encode("utf-8")

    elif topic_type == TOPICIDTYPE_PREDEFINED:
        topic_id = int(topic_input)
        payload = struct.pack(">BHH", flags, msg_id, topic_id)

    elif topic_type == TOPICIDTYPE_SHORT:
        if len(topic_input) != 2:
            print("SHORT topic deve ter exatamente 2 caracteres.")
            sys.exit(1)
        payload = struct.pack(">BH", flags, msg_id) + topic_input.encode("utf-8")

    length = len(payload) + 2
    return struct.pack(">BB", length, MQTTSN_SUBSCRIBE) + payload


def build_unsubscribe_by_topicid(topic_id, msg_id):
    flags = 0x00
    payload = struct.pack(">BHH", flags, msg_id, topic_id)
    length = len(payload) + 2
    return struct.pack(">BB", length, MQTTSN_UNSUBSCRIBE) + payload


def build_disconnect():
    return struct.pack(">BB", 2, MQTTSN_DISCONNECT)


def build_puback(topic_id, msg_id):
    payload = struct.pack(">HHB", topic_id, msg_id, 0x00)
    length = len(payload) + 2
    return struct.pack(">BB", length, MQTTSN_PUBACK) + payload


def build_pubrec(msg_id):
    return struct.pack(">BBH", 4, MQTTSN_PUBREC, msg_id)


def build_pubrel(msg_id):
    return struct.pack(">BBH", 4, MQTTSN_PUBREL, msg_id)


def build_pubcomp(msg_id):
    return struct.pack(">BBH", 4, MQTTSN_PUBCOMP, msg_id)


def build_pingreq():
    return struct.pack(">BB", 2, MQTTSN_PINGREQ)

# =============================================================================
# 4. Subscriber MQTT-SN
# =============================================================================

def mqttsn_subscriber():

    local_port = 1893
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, local_port))
    sock.settimeout(1)

    keep_alive = 30
    last_tx_time = time.time()
    awaiting_pingresp = False
    ping_sent_time = 0

    print(f"Subscriber iniciado em {CLIENT_IP}:{local_port}")
    print(f"Gateway em {GW_IP}:{GW_PORT}\n")

    topic_input = input("Digite o tópico ou ID: ").strip()

    topic_type_choice = input("Tipo (0=TopicName, 1=Predefined, 2=Short): ").strip()
    topic_type = {
        "0": TOPICIDTYPE_TOPICNAME,
        "1": TOPICIDTYPE_PREDEFINED,
        "2": TOPICIDTYPE_SHORT
    }.get(topic_type_choice, TOPICIDTYPE_TOPICNAME)

    qos_choice = input("Digite o nível de QoS (0, 1, 2): ").strip()
    qos_level = {"0": QOS_0, "1": QOS_1, "2": QOS_2}.get(qos_choice, QOS_0)

    # CONNECT
    sock.sendto(build_connect(), (GW_IP, GW_PORT))
    last_tx_time = time.time()
    print("-> CONNECT enviado")

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            _, msgType = struct.unpack(">BB", data[:2])
            if msgType == MQTTSN_CONNACK:
                print("<- CONNACK recebido")
                break
        except socket.timeout:
            continue

    # SUBSCRIBE
    msg_id = random.randint(1, 2000)
    sock.sendto(build_subscribe(topic_input, msg_id, qos_level, topic_type), (GW_IP, GW_PORT))
    last_tx_time = time.time()
    print("-> SUBSCRIBE enviado")

    topic_id = None

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            _, msgType = struct.unpack(">BB", data[:2])
            if msgType == MQTTSN_SUBACK:
                topic_id = struct.unpack(">H", data[3:5])[0]
                print(f"<- SUBACK recebido. Topic ID = {topic_id}\n")
                break
        except socket.timeout:
            continue

    print("Aguardando mensagens...\n")

    while True:
        try:
            data, _ = sock.recvfrom(8192)
        except socket.timeout:
            continue

        length, msgType = struct.unpack(">BB", data[:2])

        if msgType == MQTTSN_PUBLISH:

            flags = data[2]
            qos_bits = (flags >> 5) & 0x03
            retain = (flags >> 4) & 0x01
            topic_id_enc = struct.unpack(">H", data[3:5])[0]
            msg_id_rcv = struct.unpack(">H", data[5:7])[0]
            raw_payload = data[7:]

            topic_id_rcv = topic_id_enc ^ SECRET_TOPIC_ID
            decoded_bytes = xor_data(raw_payload, SECRET_DATA_PUBLISH)
            payload = decoded_bytes.decode("utf-8", errors="ignore").rstrip("*")

            print(f"<- PUBLISH recebido: TopicID={topic_id_rcv}, QoS={qos_bits}, Retain={retain}")
            print(f"   Conteúdo: '{payload}'")

            if qos_bits == QOS_1:
                sock.sendto(build_puback(topic_id_rcv, msg_id_rcv), (GW_IP, GW_PORT))

            elif qos_bits == QOS_2:
                sock.sendto(build_pubrec(msg_id_rcv), (GW_IP, GW_PORT))

        elif msgType == MQTTSN_PUBREL:
            msg_id = struct.unpack(">H", data[2:4])[0]
            sock.sendto(build_pubcomp(msg_id), (GW_IP, GW_PORT))

        elif msgType == MQTTSN_PINGRESP:
            awaiting_pingresp = False

        elif msgType == MQTTSN_DISCONNECT:
            print("Gateway encerrou conexão.")
            break


# =============================================================================
# Execução Principal
# =============================================================================

if __name__ == "__main__":
    mqttsn_subscriber()