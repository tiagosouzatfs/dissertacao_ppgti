#!/usr/bin/env python3
import socket
import struct
import random
import time

# =============================================================================
# Constantes MQTT-SN
# =============================================================================

MQTTSN_CONNECT     = 0x04
MQTTSN_CONNACK     = 0x05
MQTTSN_REGISTER    = 0x0A
MQTTSN_REGACK      = 0x0B
MQTTSN_PUBLISH     = 0x0C
MQTTSN_PUBACK      = 0x0D
MQTTSN_PUBREC      = 0x0F
MQTTSN_PUBREL      = 0x10
MQTTSN_PUBCOMP     = 0x0E
MQTTSN_DISCONNECT  = 0x18

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_TOPICNAME        = 0b00
TOPICIDTYPE_PREDEFINEDTOPIC  = 0b01
TOPICIDTYPE_SHORTTOPICNAME   = 0b10

GW_IP = "10.0.0.1"
GW_PORT = 1884
CLIENT_IP = "10.0.0.2"
CLIENT_PORT = 55000

SERVER_ADDRESS = (GW_IP, GW_PORT)

selected_topic_type = TOPICIDTYPE_TOPICNAME
retain_flag = 0


# =============================================================================
# Funções auxiliares
# =============================================================================

def send_and_receive(sock, packet, timeout=3):
    sock.sendto(packet, SERVER_ADDRESS)
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
        if len(data) < 2:
            print("<- ERRO: payload MQTT-SN muito curto")
            return None
        length, msgType = struct.unpack('>BB', data[:2])
        print(f"<- Recebido: Tipo {hex(msgType)} (len={length})")
        return data
    except socket.timeout:
        print("<- ERRO: Timeout")
        return None


def recv_only(sock, timeout=3):
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
        if len(data) < 2:
            print("Recebido payload MQTT-SN muito curto")
            return None
        length, msgType = struct.unpack('>BB', data[:2])
        print(f"<- Recebido: Tipo {hex(msgType)} (len={length})")
        return data
    except socket.timeout:
        print("<- ERRO: Timeout")
        return None


def xor_data(data_str, mask_int):
    data_bytes = data_str.encode("utf-8")
    mask_bytes = mask_int.to_bytes(64, 'big')
    return bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])


# =============================================================================
# Construção de pacotes MQTT-SN
# =============================================================================

def build_connect(client_id, duration=30):
    flags = 0x04
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode('utf-8')
    return struct.pack('>BB', len(payload) + 2, MQTTSN_CONNECT) + payload


def build_register(topic_name, msg_id):
    topic_id = 0x0000
    payload = struct.pack('>HH', topic_id, msg_id) + topic_name.encode('utf-8')
    return struct.pack('>BB', len(payload) + 2, MQTTSN_REGISTER) + payload


def build_publish(qos_level, topic_id, msg_id, data):
    retain_bit = (retain_flag & 0x01) << 4 if qos_level != QOS_M1 else 0
    flags = ((qos_level & 0x03) << 5) | (selected_topic_type & 0x03) | retain_bit

    topic_id_enc = topic_id ^ SECRET_TOPIC_ID
    msg_id_to_send = msg_id if qos_level != QOS_M1 else 0x0000

    header = struct.pack('>BHH', flags, topic_id_enc, msg_id_to_send)
    payload = data if isinstance(data, (bytes, bytearray)) else data.encode('utf-8')
    length = len(header) + len(payload) + 2

    return struct.pack('>BB', length, MQTTSN_PUBLISH) + header + payload


def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    return struct.pack('>BB', len(payload) + 2, MQTTSN_PUBREL) + payload


def build_disconnect():
    return struct.pack('>BB', 2, MQTTSN_DISCONNECT)


# =============================================================================
# Sequência principal
# =============================================================================

def sequence_common(sock, qos_level, msg_id, topic_name, data, client_id):

    data_bytes = xor_data(data, SECRET_DATA_PUBLISH)

    if qos_level == QOS_M1:
        publish_packet = build_publish(qos_level, topic_name, 0x0000, data_bytes)
        print("-> Enviando: PUBLISH (QoS -1)")
        sock.sendto(publish_packet, SERVER_ADDRESS)
        return

    print(f"-> Enviando: CONNECT ({client_id})")
    if not send_and_receive(sock, build_connect(client_id)):
        return

    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        print("-> Enviando: REGISTER")
        regack = send_and_receive(sock, build_register(topic_name, msg_id))
        if not regack:
            return
        topic_id = struct.unpack('>H', regack[2:4])[0]
    else:
        topic_id = topic_name

    print("-> Enviando: PUBLISH")
    sock.sendto(build_publish(qos_level, topic_id, msg_id, data_bytes), SERVER_ADDRESS)

    if qos_level == QOS_0:
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        return

    if qos_level == QOS_1:
        recv_only(sock)
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        return

    if qos_level == QOS_2:
        pubrec = recv_only(sock)
        if pubrec:
            sock.sendto(build_pubrel(msg_id), SERVER_ADDRESS)
            recv_only(sock)
        sock.sendto(build_disconnect(), SERVER_ADDRESS)


# =============================================================================
# Execução principal
# =============================================================================

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))

    client_id = f"struct_client_{random.randint(1000,9999)}"

    qos_map = {"-1": QOS_M1, "0": QOS_0, "1": QOS_1, "2": QOS_2}
    qos_choice = input("QoS (-1,0,1,2): ")
    qos_level = qos_map.get(qos_choice)

    if qos_level is None:
        print("QoS inválido")
        exit(1)

    topic_type_map = {
        "0": TOPICIDTYPE_TOPICNAME,
        "1": TOPICIDTYPE_PREDEFINEDTOPIC,
        "2": TOPICIDTYPE_SHORTTOPICNAME
    }

    topic_type_choice = input("TopicIdType (0=Name,1=Predefined,2=Short): ")
    selected_topic_type = topic_type_map.get(topic_type_choice, TOPICIDTYPE_TOPICNAME)

    if qos_level != QOS_M1:
        retain_flag = 1 if input("Retain? (0/1): ") == "1" else 0

    # ===== Entrada do tópico correta =====

    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        topic_name = input("Digite o Topic Name: ")

    elif selected_topic_type == TOPICIDTYPE_PREDEFINEDTOPIC:
        topic_name = int(input("Digite o Predefined Topic ID (0-65535): "))

    elif selected_topic_type == TOPICIDTYPE_SHORTTOPICNAME:
        while True:
            short_input = input("Digite o Short Topic (2 caracteres): ")
            if len(short_input) == 2:
                topic_name = int.from_bytes(short_input.encode(), "big")
                break
            else:
                print("Deve ter exatamente 2 caracteres.")

    # ===== Entrada da mensagem =====

    while True:
        data_msg = input("Mensagem (máx 64 bytes): ")
        data_len = len(data_msg.encode("utf-8"))
        if data_len > 64:
            print("Mensagem excede 64 bytes.")
        else:
            data_msg = data_msg.ljust(64, "*")
            break

    sequence_common(sock, qos_level, 0x0001, topic_name, data_msg, client_id)

    sock.close()
    print("\n--- Fim ---")