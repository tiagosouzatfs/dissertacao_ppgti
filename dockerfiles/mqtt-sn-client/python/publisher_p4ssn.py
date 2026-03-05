#!/usr/bin/env python3
import socket
import struct
import random

# =============================================================================
# Constantes MQTT-SN
# =============================================================================

MQTTSN_CONNECT      = 0x04
MQTTSN_CONNACK      = 0x05
MQTTSN_REGISTER     = 0x0A
MQTTSN_REGACK       = 0x0B
MQTTSN_PUBLISH      = 0x0C
MQTTSN_PUBACK       = 0x0D
MQTTSN_PUBREC       = 0x0F
MQTTSN_PUBREL       = 0x10
MQTTSN_PUBCOMP      = 0x0E
MQTTSN_DISCONNECT   = 0x18

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_TOPICNAME         = 0b00
TOPICIDTYPE_PREDEFINEDTOPIC   = 0b01
TOPICIDTYPE_SHORTTOPICNAME    = 0b10

GW_IP = "10.0.0.1"
GW_PORT = 1884
CLIENT_IP = "10.0.0.2"
CLIENT_PORT = 0

SERVER_ADDRESS = (GW_IP, GW_PORT)
TIMEOUT = 5
MAX_RETRIES = 3

selected_topic_type = TOPICIDTYPE_TOPICNAME
retain_flag = 0

# =============================================================================
# Lógica OTP (One-Time Pad) - Sincronizada com P4
# =============================================================================

def generate_otp(salt):
    otp = ((salt << 7) & 0xFFFF) ^ (salt >> 9) ^ 0xA5A5
    otp = ((otp << 3) & 0xFFFF) | (otp >> 13)
    return otp & 0xFFFF

def otp_encrypt_topic(topic_id, salt):
    otp = generate_otp(salt)
    val = (topic_id ^ SECRET_TOPIC_ID ^ otp) & 0xFFFF
    return ((val << 4) | (val >> 12)) & 0xFFFF

def otp_process_data(data_str, salt_ignored):
    # Novo OTP Data: Gera salt aleatório e embuti no payload (Independente do cabeçalho)
    payload_salt = random.getrandbits(16)
    otp = generate_otp(payload_salt)
    
    # Ajusta para 62 bytes para que o total (salt + data) seja 64
    data_bytes = data_str.encode().ljust(62, b"*")[:62]
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, 'big')
    output = []
    for i, b in enumerate(data_bytes):
        dynamic_mask = mask_bytes[i % 64] ^ (otp & 0xFF if i % 2 == 0 else (otp >> 8) & 0xFF)
        output.append(b ^ dynamic_mask)
    
    # Retorna o Salt (2 bytes) + Payload Cifrado (62 bytes)
    return struct.pack('>H', payload_salt) + bytes(output)

# =============================================================================
# Comunicação robusta (Original)
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
# Construção de pacotes (Original com OTP)
# =============================================================================

def build_connect(client_id, duration=30):
    payload = struct.pack('>BBH', 0x04, 0x01, duration) + client_id.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_CONNECT) + payload

def build_register(topic_name, msg_id):
    payload = struct.pack('>HH', 0x0000, msg_id) + topic_name.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_REGISTER) + payload

def build_publish(qos_level, topic_id, msg_id, data_str):
    # Salt: Se QoS -1, gera aleatório (Nonce). Se não, usa msg_id.
    salt = msg_id if qos_level != QOS_M1 else random.randint(1, 0xFFFF)
    
    retain_bit = (retain_flag & 0x01) << 4 if qos_level != QOS_M1 else 0
    flags = ((qos_level & 0x03) << 5) | (selected_topic_type & 0x03) | retain_bit

    topic_id_enc = otp_encrypt_topic(topic_id, salt)
    
    # Altera apenas a chamada do data para usar a nova lógica de salt embutido
    data_enc = otp_process_data(data_str, salt)

    header = struct.pack('>BHH', flags, topic_id_enc, salt)
    length = len(header) + len(data_enc) + 2
    return struct.pack('>BB', length, MQTTSN_PUBLISH) + header + data_enc

def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    return struct.pack('>BB', len(payload)+2, MQTTSN_PUBREL) + payload

def build_disconnect():
    return struct.pack('>BB', 2, MQTTSN_DISCONNECT)

# =============================================================================
# Sequência principal
# =============================================================================

def sequence_common(sock, qos_level, msg_id, topic_input, data, client_id):

    # ---------------- QoS -1 ----------------
    if qos_level == QOS_M1:
        print("-> Enviando: PUBLISH (QoS -1)")
        sock.sendto(build_publish(qos_level, topic_input, 0, data), SERVER_ADDRESS)
        return

    # ---------------- CONNECT ----------------
    print(f"-> Enviando: CONNECT ({client_id})")
    if not send_and_wait(sock, build_connect(client_id), MQTTSN_CONNACK):
        return

    # ---------------- REGISTER ----------------
    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        print("-> Enviando: REGISTER")
        regack = send_and_wait(sock, build_register(topic_input, msg_id), MQTTSN_REGACK, msg_id)
        if not regack:
            return
        # CORREÇÃO: O TopicId no REGACK MQTT-SN padrão (7 bytes) está nos bytes 2 e 3
        # [0]=Len, [1]=Type(0x0B), [2:4]=TopicId, [4:6]=MsgId, [6]=ReturnCode
        topic_id = struct.unpack('>H', regack[2:4])[0]
        print(f"<- REGACK recebido: topic_id = {topic_id}")
    else:
        topic_id = topic_input

    # ---------------- PUBLISH ----------------
    print("-> Enviando: PUBLISH")
    sock.sendto(build_publish(qos_level, topic_id, msg_id, data), SERVER_ADDRESS)

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
    q_input = input("QoS (-1,0,1,2): ")
    qos_level = qos_map.get(q_input)

    if qos_level is None:
        print("QoS inválido")
        exit(1)

    topic_type_map = {"0": TOPICIDTYPE_TOPICNAME, "1": TOPICIDTYPE_PREDEFINEDTOPIC, "2": TOPICIDTYPE_SHORTTOPICNAME}

    if qos_level == QOS_M1:
        topic_type_choice = input("TopicIdType (1=Predefined,2=Short): ")
    else:
        topic_type_choice = input("TopicIdType (0=Name,1=Predefined,2=Short): ")

    selected_topic_type = topic_type_map.get(topic_type_choice)
    if qos_level != QOS_M1:
        retain_flag = 1 if input("Retain? (0/1): ") == "1" else 0

    if selected_topic_type == TOPICIDTYPE_TOPICNAME:
        topic_val = input("Digite o Topic Name: ")
    elif selected_topic_type == TOPICIDTYPE_PREDEFINEDTOPIC:
        topic_val = int(input("Digite o Predefined Topic ID: "))
    elif selected_topic_type == TOPICIDTYPE_SHORTTOPICNAME:
        # Pega 2 caracteres e converte para int de 16 bits
        t_str = input("Digite o Short Topic (2 caracteres): ")[:2].ljust(2, '_')
        topic_val = struct.unpack('>H', t_str.encode())[0]

    data_msg = input("Mensagem (máx 64 bytes): ").ljust(64, "*")[:64]

    sequence_common(sock, qos_level, 0x0001, topic_val, data_msg, client_id)
    sock.close()
    print("\n--- Fim ---")