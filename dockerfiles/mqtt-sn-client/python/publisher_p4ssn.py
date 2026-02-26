#!/usr/bin/env python3
import socket
import struct
import random

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

TIMEOUT = 5
MAX_RETRIES = 3

selected_topic_type = TOPICIDTYPE_TOPICNAME
retain_flag = 0


# =============================================================================
# Comunicação robusta
# =============================================================================

def recv_packet(sock, expected_type=None, expected_msg_id=None):
    sock.settimeout(TIMEOUT)
    try:
        data, _ = sock.recvfrom(4096)
        if len(data) < 2:
            print("<- ERRO: payload MQTT-SN muito curto")
            return None

        length, msgType = struct.unpack('>BB', data[:2])
        print(f"<- Recebido: Tipo {hex(msgType)} (len={length})")

        if expected_type and msgType != expected_type:
            print("   ERRO: Tipo inesperado")
            return None

        if expected_msg_id and len(data) >= 6:
            recv_msg_id = struct.unpack('>H', data[4:6])[0]
            if recv_msg_id != expected_msg_id:
                print("   ERRO: msgId incorreto")
                return None

        return data

    except socket.timeout:
        print("<- ERRO: Timeout")
        return None


def send_and_wait(sock, packet, expected_type=None, expected_msg_id=None):
    for attempt in range(1, MAX_RETRIES + 1):
        sock.sendto(packet, SERVER_ADDRESS)
        resp = recv_packet(sock, expected_type, expected_msg_id)
        if resp:
            return resp
        print(f"   Tentativa {attempt}/{MAX_RETRIES} falhou")
    return None


def drain_socket(sock):
    sock.settimeout(1)
    try:
        while True:
            sock.recvfrom(4096)
    except socket.timeout:
        pass


# =============================================================================
# Construção de pacotes
# =============================================================================

def build_connect(client_id, duration=30):
    payload = struct.pack('>BBH', 0x04, 0x01, duration) + client_id.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_CONNECT) + payload


def build_register(topic_name, msg_id):
    payload = struct.pack('>HH', 0x0000, msg_id) + topic_name.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_REGISTER) + payload


def build_publish(qos_level, topic_id, msg_id, data):
    retain_bit = (retain_flag & 0x01) << 4 if qos_level != QOS_M1 else 0
    flags = ((qos_level & 0x03) << 5) | (selected_topic_type & 0x03) | retain_bit

    topic_id_enc = topic_id ^ SECRET_TOPIC_ID
    msg_id_to_send = msg_id if qos_level != QOS_M1 else 0x0000

    header = struct.pack('>BHH', flags, topic_id_enc, msg_id_to_send)
    length = len(header) + len(data) + 2

    return struct.pack('>BB', length, MQTTSN_PUBLISH) + header + data


def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    return struct.pack('>BB', len(payload)+2, MQTTSN_PUBREL) + payload


def build_disconnect():
    return struct.pack('>BB', 2, MQTTSN_DISCONNECT)


def xor_data(data_str):
    data_bytes = data_str.encode()
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, 'big')
    return bytes([b ^ mask_bytes[i % 64] for i, b in enumerate(data_bytes)])


# =============================================================================
# Sequência principal
# =============================================================================

def sequence_common(sock, qos_level, msg_id, topic_name, data, client_id):

    data_bytes = xor_data(data)

    # ---------------- QoS -1 ----------------
    if qos_level == QOS_M1:
        print("-> Enviando: PUBLISH (QoS -1)")
        sock.sendto(build_publish(qos_level, topic_name, 0, data_bytes), SERVER_ADDRESS)
        return

    # ---------------- CONNECT ----------------
    print(f"-> Enviando: CONNECT ({client_id})")
    if not send_and_wait(sock, build_connect(client_id), MQTTSN_CONNACK):
        return

    # ---------------- REGISTER ----------------
    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        print("-> Enviando: REGISTER")
        regack = send_and_wait(sock, build_register(topic_name, msg_id), MQTTSN_REGACK, msg_id)
        if not regack:
            return
        topic_id = struct.unpack('>H', regack[2:4])[0]
    else:
        topic_id = topic_name

    # ---------------- PUBLISH ----------------
    print("-> Enviando: PUBLISH")
    sock.sendto(build_publish(qos_level, topic_id, msg_id, data_bytes), SERVER_ADDRESS)

    if qos_level == QOS_0:
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        drain_socket(sock)
        return

    if qos_level == QOS_1:
        if not recv_packet(sock, MQTTSN_PUBACK, msg_id):
            return
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        drain_socket(sock)
        return

    if qos_level == QOS_2:
        if not recv_packet(sock, MQTTSN_PUBREC, msg_id):
            return
        sock.sendto(build_pubrel(msg_id), SERVER_ADDRESS)
        if not recv_packet(sock, MQTTSN_PUBCOMP, msg_id):
            return
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        drain_socket(sock)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))

    client_id = f"struct_client_{random.randint(1000,9999)}"

    qos_map = {"-1": QOS_M1, "0": QOS_0, "1": QOS_1, "2": QOS_2}
    qos_level = qos_map.get(input("QoS (-1,0,1,2): "))

    if qos_level is None:
        print("QoS inválido")
        exit(1)

    topic_type_map = {
        "0": TOPICIDTYPE_TOPICNAME,
        "1": TOPICIDTYPE_PREDEFINEDTOPIC,
        "2": TOPICIDTYPE_SHORTTOPICNAME
    }

    # QoS -1 restrições
    if qos_level == QOS_M1:
        print("QoS -1: apenas Predefined ou Short Topic permitido.")
        topic_type_choice = input("TopicIdType (1=Predefined,2=Short): ")
        if topic_type_choice == "0":
            print("Topic Name não permitido para QoS -1")
            exit(1)
    else:
        topic_type_choice = input("TopicIdType (0=Name,1=Predefined,2=Short): ")

    selected_topic_type = topic_type_map.get(topic_type_choice)

    if selected_topic_type is None:
        print("Tipo de tópico inválido")
        exit(1)

    if qos_level != QOS_M1:
        retain_flag = 1 if input("Retain? (0/1): ") == "1" else 0

    # Entrada de tópico
    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        topic_name = input("Digite o Topic Name: ")

    elif selected_topic_type == TOPICIDTYPE_PREDEFINEDTOPIC:
        topic_name = int(input("Digite o Predefined Topic ID: "))

    elif selected_topic_type == TOPICIDTYPE_SHORTTOPICNAME:
        while True:
            short_input = input("Digite o Short Topic (2 caracteres): ")
            if len(short_input) == 2:
                topic_name = int.from_bytes(short_input.encode(), "big")
                break
            else:
                print("Deve ter exatamente 2 caracteres.")

    # Mensagem
    while True:
        data_msg = input("Mensagem (máx 64 bytes): ")
        if len(data_msg.encode()) <= 64:
            data_msg = data_msg.ljust(64, "*")
            break
        print("Mensagem excede 64 bytes.")

    sequence_common(sock, qos_level, 0x0001, topic_name, data_msg, client_id)

    sock.close()
    print("\n--- Fim ---")