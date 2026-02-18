#!/usr/bin/env python3
# sub.py — MQTT-SN subscriber com (compatível com publisher)

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

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0xA3F19C7E4B2D8F0165E7C9A4B3D2F18C9E7A6B5C4D3F21987A1C2D3E4F5061728394A5B6C7D8E9F01A2B3C4D5E6F708192A3B4C5D6E7F809ABCDEF0123456789FEDCBA9876543210

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

def build_connect(client_id=None, duration=60):
    flags = 0x02
    protocol_id = 0x01
    if client_id is None:
        client_id = f"sub_client_{random.randint(1000,9999)}".encode()
    payload = struct.pack(">BBH", flags, protocol_id, duration) + client_id
    length = len(payload) + 2
    return struct.pack(">BB", length, MQTTSN_CONNECT) + payload

def build_subscribe(topic_name, msg_id, qos_level):
    flags = (1 << 7) | (qos_level << 5)
    payload = struct.pack(">BH", flags, msg_id) + topic_name.encode("utf-8")
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

# =============================================================================
# 4. Subscriber MQTT-SN
# =============================================================================

def mqttsn_subscriber():
    local_port = random.randint(46000, 49000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, local_port))
    sock.settimeout(1)

    print(f"Subscriber iniciado em {CLIENT_IP}:{local_port}")
    print(f"Gateway em {GW_IP}:{GW_PORT}\n")

    topic = input("Digite o tópico para inscrever: ").strip()
    qos_choice = input("Digite o nível de QoS (0, 1, 2): ").strip()
    qos_level = {"0": QOS_0, "1": QOS_1, "2": QOS_2}.get(qos_choice, QOS_0)

    # CONNECT
    sock.sendto(build_connect(), (GW_IP, GW_PORT))
    print("-> CONNECT enviado")

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if len(data) < 2:
                continue
            _, msgType = struct.unpack(">BB", data[:2])
            if msgType == MQTTSN_CONNACK:
                print("<- CONNACK recebido")
                break
        except socket.timeout:
            continue

    # SUBSCRIBE
    msg_id = random.randint(1, 2000)
    sock.sendto(build_subscribe(topic, msg_id, qos_level), (GW_IP, GW_PORT))
    print(f"-> SUBSCRIBE enviado ({topic}, QoS={qos_choice})")

    topic_id = None
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if len(data) < 2:
                continue
            _, msgType = struct.unpack(">BB", data[:2])
            if msgType == MQTTSN_SUBACK:
                topic_id = struct.unpack(">H", data[3:5])[0]
                print(f"<- SUBACK recebido. Topic ID = {topic_id}. Aguardando mensagens...\n")
                break
        except socket.timeout:
            continue

    try:
        while True:
            try:
                data, _ = sock.recvfrom(8192)
            except socket.timeout:
                continue

            if len(data) < 2:
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

                print(f"<- PUBLISH recebido: TopicID={topic_id_rcv}, QoS={qos_bits}, Retain={retain}, MsgID={msg_id_rcv}")
                print(f"   Conteúdo decodificado: '{payload}'")

                if qos_bits == QOS_1:
                    sock.sendto(build_puback(topic_id_rcv, msg_id_rcv), (GW_IP, GW_PORT))
                    print("-> PUBACK enviado\n")

                elif qos_bits == QOS_2:
                    sock.sendto(build_pubrec(msg_id_rcv), (GW_IP, GW_PORT))
                    print("-> PUBREC enviado\n")

            elif msgType == MQTTSN_PUBREL:
                msg_id = struct.unpack(">H", data[2:4])[0]
                sock.sendto(build_pubcomp(msg_id), (GW_IP, GW_PORT))
                print(f"-> PUBCOMP enviado (MsgID={msg_id})\n")

            elif msgType == MQTTSN_UNSUBACK:
                print("<- UNSUBACK recebido")

            elif msgType == MQTTSN_PINGRESP:
                print("<- PINGRESP recebido")

            elif msgType == MQTTSN_DISCONNECT:
                print("<- DISCONNECT recebido do gateway")
                break

    except KeyboardInterrupt:
        print("\nEncerrando subscriber...")

        if topic_id is not None:
            unsub_msgid = random.randint(2001, 3000)
            sock.sendto(build_unsubscribe_by_topicid(topic_id, unsub_msgid), (GW_IP, GW_PORT))
            print("-> UNSUBSCRIBE enviado")

        sock.sendto(build_disconnect(), (GW_IP, GW_PORT))
        print("-> DISCONNECT enviado")

        sock.close()
        sys.exit(0)

# =============================================================================
# Execução Principal
# =============================================================================

if __name__ == "__main__":
    mqttsn_subscriber()
