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
MQTTSN_DISCONNECT   = 0x18

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
CLIENT_PORT = 0

SERVER_ADDRESS = (GW_IP, GW_PORT)
TIMEOUT = 5


def build_connect(client_id, duration=30):
    # Flags: CleanSession=1 (0x04)
    flags = 0x04 
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode()
    # Length inclui: len_byte(1) + type_byte(1) + payload
    return struct.pack('>BB', len(payload) + 2, MQTTSN_CONNECT) + payload

def build_publish(qos_level, topic_id, msg_id, data_str, topic_type):
    # No QoS -1, retain deve ser 0 e TopicIdType deve ser Predefined(01) ou Short(02)
    retain_bit = 0
    if qos_level != QOS_M1:
        # Aqui você pode definir se quer retain nos outros níveis
        retain_bit = 0 
    
    # Flags: QoS (bits 6-5), Retain (bit 4), TopicIdType (bits 1-0)
    flags = ((qos_level & 0x03) << 5) | (retain_bit << 4) | (topic_type & 0x03)

    payload = data_str.encode()
    # No QoS -1, Message ID deve ser 0
    actual_msg_id = msg_id if qos_level != QOS_M1 else 0x0000
    
    header = struct.pack('>BHH', flags, topic_id, actual_msg_id)
    return struct.pack('>BB', len(header) + len(payload) + 2, MQTTSN_PUBLISH) + header + payload

def build_disconnect():
    return struct.pack('>BB', 2, MQTTSN_DISCONNECT)

# --- Fluxo Principal ---

def run_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))
    sock.settimeout(TIMEOUT)
    
    client_id = f"cli_{random.randint(100, 999)}"
    
    # Inputs do usuário
    q_in = input("QoS (-1, 0, 1, 2): ")
    qos_level = {"-1": QOS_M1, "0": QOS_0, "1": QOS_1, "2": QOS_2}.get(q_in, QOS_0)
    
    if qos_level == QOS_M1:
        print("Para QoS -1, use Predefined (1) ou Short (2)")
        t_type = int(input("TopicIdType (1=Predefined, 2=Short): "))
    else:
        t_type = int(input("TopicIdType (0=Name, 1=Predefined, 2=Short): "))

    # CONNECT (Obrigatório para o Bisquitt estabilizar a ponte MQTT)
    print(f"-> Enviando CONNECT ({client_id})...")
    sock.sendto(build_connect(client_id), SERVER_ADDRESS)
    try:
        data, _ = sock.recvfrom(1024)
        if data[1] == MQTTSN_CONNACK:
            print("<- CONNACK recebido (Sessão Ativa)")
    except:
        print("!! Aviso: Sem resposta de CONNACK, tentando seguir...")

    if t_type == TOPICIDTYPE_PREDEFINEDTOPIC:
        topic_val = int(input("ID do Tópico Pré-definido (ex: 20): "))
    elif t_type == TOPICIDTYPE_SHORTTOPICNAME:
        t_str = input("Short Topic (2 chars): ")[:2].ljust(2, '_')
        topic_val = struct.unpack('>H', t_str.encode())[0]
    else:
        # Registro de tópico para QoS 0, 1, 2
        topic_name = input("Nome do Tópico: ")
        reg_pkt = struct.pack('>BBHH', len(topic_name)+6, MQTTSN_REGISTER, 0, 1) + topic_name.encode()
        sock.sendto(reg_pkt, SERVER_ADDRESS)
        regack, _ = sock.recvfrom(1024)
        topic_val = struct.unpack('>H', regack[2:4])[0]
        print(f"<- Topic Registered ID: {topic_val}")

    msg = input("Mensagem: ")
    print(f"-> Enviando PUBLISH QoS {q_in}...")
    pub_pkt = build_publish(qos_level, topic_val, 0x0001, msg, t_type)
    sock.sendto(pub_pkt, SERVER_ADDRESS)

    if qos_level != QOS_M1:
        time.sleep(0.5)
        sock.sendto(build_disconnect(), SERVER_ADDRESS)
        print("-> DISCONNECT enviado.")
    
    sock.close()
    print("--- Teste Finalizado ---")

if __name__ == "__main__":
    run_test()