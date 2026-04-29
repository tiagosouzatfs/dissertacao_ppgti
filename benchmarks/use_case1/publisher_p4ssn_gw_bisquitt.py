#!/usr/bin/env python3
import socket
import struct
import random
import time

# Constantes MQTT-SN

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

# Segurança P4SSN
SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_TOPICNAME         = 0b00
TOPICIDTYPE_PREDEFINEDTOPIC   = 0b01
TOPICIDTYPE_SHORTTOPICNAME    = 0b10

GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.3"

SERVER_ADDRESS = (GW_IP, GW_PORT)
TIMEOUT = 5

# Lógica OTP (One-Time Pad) - Sincronizada com P4

def generate_otp(salt):
    otp = ((salt << 7) & 0xFFFF) ^ (salt >> 9) ^ 0xA5A5
    otp = ((otp << 3) & 0xFFFF) | (otp >> 13)
    return otp & 0xFFFF

def otp_encrypt_topic(topic_id, salt):
    otp = generate_otp(salt)
    val = (topic_id ^ SECRET_TOPIC_ID ^ otp) & 0xFFFF
    return ((val << 4) | (val >> 12)) & 0xFFFF

def otp_process_data(data_str, salt_ignored):
    payload_salt = random.getrandbits(16)
    otp = generate_otp(payload_salt)
    data_bytes = data_str.encode().ljust(62, b"*")[:62]
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, 'big')
    output = []
    for i, b in enumerate(data_bytes):
        dynamic_mask = mask_bytes[i % 64] ^ (otp & 0xFF if i % 2 == 0 else (otp >> 8) & 0xFF)
        output.append(b ^ dynamic_mask)
    return struct.pack('>H', payload_salt) + bytes(output)

# Comunicação
def drain_socket(sock):
    sock.settimeout(1)
    try:
        while True:
            sock.recvfrom(4096)
    except:
        pass

def recv_packet(sock, expected_type=None):
    try:
        data, _ = sock.recvfrom(1024)
        if len(data) < 2: return None
        _, msgType = struct.unpack('>BB', data[:2])
        if expected_type and msgType != expected_type: return None
        return data
    except:
        return None

# Construção de pacotes (com OTP)
def build_connect(client_id, duration=60):
    flags = 0x04 # Clean Session
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_CONNECT) + payload

def build_publish(qos_level, topic_id, msg_id, data_str, topic_type, retain_flag):
    # No QoS -1, salt é randômico. Nos outros, usa o msg_id.
    salt = msg_id if qos_level != QOS_M1 else random.randint(1, 0xFFFF)
    
    retain_bit = (retain_flag & 0x01) << 4 if qos_level != QOS_M1 else 0
    flags = ((qos_level & 0x03) << 5) | (topic_type & 0x03) | retain_bit
    
    topic_id_enc = otp_encrypt_topic(topic_id, salt)
    data_enc = otp_process_data(data_str, salt)
    
    actual_msg_id = msg_id if qos_level != QOS_M1 else 0x0000
    
    header = struct.pack('>BHH', flags, topic_id_enc, actual_msg_id)
    return struct.pack('>BB', len(header) + len(data_enc) + 2, MQTTSN_PUBLISH) + header + data_enc

def build_register(topic_name, msg_id):
    payload = struct.pack('>HH', 0x0000, msg_id) + topic_name.encode()
    return struct.pack('>BB', len(payload)+2, MQTTSN_REGISTER) + payload

# Sequência principal
def execute_p4ssn_flow(qos_level, topic_type, topic_input, data_msg, retain_flag):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))
    sock.settimeout(TIMEOUT)
    client_id = f"p4_cli_{random.randint(1000,9999)}"
    msg_id = 0x0001

    try:
        # CONNECT (Obrigatório para o Gateway estabilizar a sessão)
        print(f"-> Enviando: CONNECT ({client_id})")
        sock.sendto(build_connect(client_id), SERVER_ADDRESS)
        connack = recv_packet(sock, MQTTSN_CONNACK)
        if connack:
            print("<- CONNACK recebido")
        else:
            print("!! Aviso: Sem resposta de CONNACK, prosseguindo...")

        # REGISTER (Apenas se for Topic Name e não for QoS -1)
        topic_id = topic_input
        if qos_level != QOS_M1 and topic_type == TOPICIDTYPE_TOPICNAME:
            print("-> Enviando: REGISTER")
            sock.sendto(build_register(topic_input, msg_id), SERVER_ADDRESS)
            regack = recv_packet(sock, MQTTSN_REGACK)
            if regack:
                topic_id = struct.unpack('>H', regack[2:4])[0]
                print(f"<- REGACK recebido: ID {topic_id}")
            else:
                print("!! Erro no Registro de Tópico")
                return

        # PUBLISH (Criptografado P4SSN)
        print(f"-> Enviando: PUBLISH QoS {qos_level}")
        pub_pkt = build_publish(qos_level, topic_id, msg_id, data_msg, topic_type, retain_flag)
        sock.sendto(pub_pkt, SERVER_ADDRESS)

        # Handshake de Confirmação (QoS 1 e 2)
        if qos_level == QOS_1:
            recv_packet(sock, MQTTSN_PUBACK)
        elif qos_level == QOS_2:
            if recv_packet(sock, MQTTSN_PUBREC):
                sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), SERVER_ADDRESS)
                recv_packet(sock, MQTTSN_PUBCOMP)

        # DISCONNECT (Limpeza da sessão no Gateway)
        time.sleep(0.1)
        sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), SERVER_ADDRESS)
        print("-> DISCONNECT enviado.")
        drain_socket(sock)

    except Exception as e:
        print(f"Erro no fluxo: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    q_in = input("QoS (-1, 0, 1, 2): ")
    qos_level = {"-1": QOS_M1, "0": QOS_0, "1": QOS_1, "2": QOS_2}.get(q_in, QOS_0)

    if qos_level == QOS_M1:
        print("Para QoS -1, use Predefined (1) ou Short (2)")
        t_choice = input("TopicIdType (1=Predefined, 2=Short): ")
    else:
        t_choice = input("TopicIdType (0=Name, 1=Predefined, 2=Short): ")
    
    t_type_map = {"0": TOPICIDTYPE_TOPICNAME, "1": TOPICIDTYPE_PREDEFINEDTOPIC, "2": TOPICIDTYPE_SHORTTOPICNAME}
    topic_type = t_type_map.get(t_choice, TOPICIDTYPE_PREDEFINEDTOPIC)

    retain_flag = 1 if qos_level != QOS_M1 and input("Retain? (0/1): ") == "1" else 0

    if topic_type == TOPICIDTYPE_TOPICNAME:
        topic_val = input("Digite o Nome do Tópico: ")
    elif topic_type == TOPICIDTYPE_PREDEFINEDTOPIC:
        topic_val = int(input("Digite o ID Pré-definido: "))
    else:
        t_str = input("Digite o Short Topic (2 caracteres): ")[:2].ljust(2, '_')
        topic_val = struct.unpack('>H', t_str.encode())[0]

    data_msg = input("Mensagem: ")

    execute_p4ssn_flow(qos_level, topic_type, topic_val, data_msg, retain_flag)
    print("--- Fim ---")