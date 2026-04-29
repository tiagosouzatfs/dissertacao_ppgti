#!/usr/bin/env python3
import socket
import struct
import random
import time

# Constantes MQTT-SN

MQTTSN_CONNECT      = 0x04
MQTTSN_CONNACK      = 0x05
MQTTSN_SUBSCRIBE    = 0x12
MQTTSN_SUBACK       = 0x13
MQTTSN_PUBLISH      = 0x0C
MQTTSN_DISCONNECT   = 0x18
MQTTSN_PINGREQ      = 0x16
MQTTSN_PINGRESP     = 0x17
MQTTSN_PUBACK       = 0x0D
MQTTSN_PUBREC       = 0x0F
MQTTSN_PUBREL       = 0x10
MQTTSN_PUBCOMP      = 0x0E

QOS_0 = 0b00
QOS_1 = 0b01
QOS_2 = 0b10

TOPICIDTYPE_TOPICNAME  = 0b00
TOPICIDTYPE_PREDEFINED = 0b01
TOPICIDTYPE_SHORT      = 0b10

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.7"
CLIENT_PORT = 1897

TIMEOUT = 5
#KEEPALIVE = 30
KEEPALIVE = 720

# Lógica OTP (One-Time Pad) - Sincronizada com P4

def generate_otp(salt):
    otp = ((salt << 7) & 0xFFFF) ^ (salt >> 9) ^ 0xA5A5
    otp = ((otp << 3) & 0xFFFF) | (otp >> 13)
    return otp & 0xFFFF

def otp_decrypt_topic(encrypted_topic, salt):
    otp = generate_otp(salt)
    # Reverte Rotação (Direita)
    val = ((encrypted_topic >> 4) | (encrypted_topic << 12)) & 0xFFFF
    return val ^ otp ^ SECRET_TOPIC_ID

def otp_process_data(payload_raw, salt_ignored):
    # Extrai o salt de 2 bytes do início do payload recebido
    payload_salt = struct.unpack('>H', payload_raw[:2])[0]
    encrypted_data = payload_raw[2:]
    
    otp = generate_otp(payload_salt)
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, "big")
    output = []
    for i, b in enumerate(encrypted_data):
        dynamic_mask = mask_bytes[i % 64] ^ (otp & 0xFF if i % 2 == 0 else (otp >> 8) & 0xFF)
        output.append(b ^ dynamic_mask)
    return bytes(output)

# Comunicação e Builders

def recv_packet(sock):
    sock.settimeout(TIMEOUT)
    try:
        data, _ = sock.recvfrom(8192)
        if len(data) < 2:
            return None
        length, msgType = struct.unpack(">BB", data[:2])
        return msgType, data
    except socket.timeout:
        return None

def build_connect(client_id, duration=KEEPALIVE):
    # Forçado Clean Session 0x04 para estabilidade no Benchmark
    payload = struct.pack(">BBH", 0x04, 0x01, duration) + client_id.encode()
    return struct.pack(">BB", len(payload)+2, MQTTSN_CONNECT) + payload

def build_subscribe(topic_input, msg_id, qos_level, topic_type):
    flags = (qos_level << 5) | topic_type
    if topic_type == TOPICIDTYPE_TOPICNAME:
        payload = struct.pack(">BH", flags, msg_id) + topic_input.encode()
    elif topic_type == TOPICIDTYPE_PREDEFINED:
        payload = struct.pack(">BHH", flags, msg_id, int(topic_input))
    else: # Short
        payload = struct.pack(">BH", flags, msg_id) + topic_input[:2].encode()
    return struct.pack(">BB", len(payload)+2, MQTTSN_SUBSCRIBE) + payload

def build_puback(topic_id, msg_id):
    payload = struct.pack(">HHB", topic_id, msg_id, 0x00)
    return struct.pack(">BB", len(payload)+2, MQTTSN_PUBACK) + payload

# Subscriber

def p4ssn_subscriber():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))
    client_id = f"p4ssn_sub_{random.randint(1000,9999)}"

    topic_input = input("Digite o tópico ou ID: ").strip()
    topic_type = int(input("Tipo (0=Name,1=Predefined,2=Short): ").strip())
    qos_level = int(input("QoS (0,1,2): ").strip())

    # CONNECT
    sock.sendto(build_connect(client_id), (GW_IP, GW_PORT))
    while True:
        pkt = recv_packet(sock)
        if pkt and pkt[0] == MQTTSN_CONNACK:
            break

    # SUBSCRIBE
    msg_id = random.randint(1, 0xFFFF)
    sock.sendto(build_subscribe(topic_input, msg_id, qos_level, topic_type), (GW_IP, GW_PORT))
    while True:
        pkt = recv_packet(sock)
        if pkt and pkt[0] == MQTTSN_SUBACK:
            break

    print("Aguardando mensagens ...\n")
    last_ping = time.time()
    msg_count = 0  # Contador de mensagens

    with open("/app/p4ssn/time_publication_p4ssn4.csv", "w") as f:
        f.write("id,t_pub_ms\n")
        while True:
            pkt = recv_packet(sock)
            t_chegada = time.time() # Captura imediata na chegada

            if pkt is None:
                if time.time() - last_ping > KEEPALIVE:
                    sock.sendto(struct.pack(">BB", 2, MQTTSN_PINGREQ), (GW_IP, GW_PORT))
                    last_ping = time.time()
                continue

            msgType, data = pkt
            if msgType == MQTTSN_PUBLISH:
                msg_count += 1
                flags = data[2]
                qos_bits = (flags >> 5) & 0x03
                
                # Decodificação OTP usando o msgId (Salt)
                topic_enc = struct.unpack(">H", data[3:5])[0]
                salt = struct.unpack(">H", data[5:7])[0]
                payload_raw = data[7:]

                topic_id_rcv = otp_decrypt_topic(topic_enc, salt)
                
                # Altera apenas a chamada do data para usar a nova lógica de salt embutido
                decoded = otp_process_data(payload_raw, salt).decode(errors="ignore").rstrip("*")

                # Cálculo de tempo de publicação
                try:
                    t_saida = float(decoded.split('_')[-1])
                    latencia = (t_chegada - t_saida) * 1000
                    f.write(f"{msg_count},{latencia:.4f}\n")
                    f.flush()
                except:
                    latencia = 0

                print(f"## PUBLISH {msg_count} (Tempo de Publicação: {latencia:.3f}ms)")
                print(f"## Conteúdo: '{decoded}'\n")

                if qos_bits == QOS_1:
                    sock.sendto(build_puback(topic_id_rcv, salt), (GW_IP, GW_PORT))
                elif qos_bits == QOS_2:
                    sock.sendto(struct.pack(">BBH", 4, MQTTSN_PUBREC, salt), (GW_IP, GW_PORT))

            elif msgType == MQTTSN_PUBREL:
                msg_id_rel = struct.unpack(">H", data[2:4])[0]
                sock.sendto(struct.pack(">BBH", 4, MQTTSN_PUBCOMP, msg_id_rel), (GW_IP, GW_PORT))
            
            elif msgType == MQTTSN_PINGRESP:
                last_ping = time.time()

if __name__ == "__main__":
    p4ssn_subscriber()