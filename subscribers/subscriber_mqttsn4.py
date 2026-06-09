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

GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.7"
CLIENT_PORT = 1897

TIMEOUT = 5
KEEPALIVE = 720

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

def mqttsn_subscriber():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, CLIENT_PORT))
    client_id = f"mqttsn_sub_{random.randint(1000,9999)}"

    topic_input = input("Digite o tópico ou ID: ").strip()
    topic_type = int(input("Tipo (0=Name, 1=Predefined, 2=Short): ").strip())
    qos_level = QOS_0  # Alteração: QoS fixado em 0

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

    with open("/app/mqtt-sn/time_publication_mqttsn4.csv", "w") as f:
        f.write("id,t_pub_ms,qos\n")
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
                
                # Extração padrão MQTT-SN: TopicID(2 bytes), MsgId(2 bytes)
                topic_id_rcv = struct.unpack(">H", data[3:5])[0]
                msg_id_rcv = struct.unpack(">H", data[5:7])[0]

                # No MQTT-SN, o payload começa no byte 7
                decoded = data[7:].decode(errors="ignore")

                # Cálculo de tempo de publicação
                try:
                    t_saida = float(decoded.split('_')[-1])
                    latencia = (t_chegada - t_saida) * 1000
                    
                    # Alteração: Lógica para extrair o QoS do payload
                    qos_payload = ""
                    if "qos_m1_" in decoded:
                        qos_payload = "-1"
                    elif "qos_0_" in decoded:
                        qos_payload = "0"
                        
                    f.write(f"{msg_count},{latencia:.4f},{qos_payload}\n")
                    f.flush()
                except:
                    latencia = 0

                print(f"## PUBLISH {msg_count} - Tempo de Publicação: {latencia:.4f}ms - Nível de QoS: {qos_payload}")
                print(f"## Conteúdo: '{decoded}'\n")

                if qos_bits == QOS_1:
                    sock.sendto(build_puback(topic_id_rcv, msg_id_rcv), (GW_IP, GW_PORT))
                elif qos_bits == QOS_2:
                    sock.sendto(struct.pack(">BBH", 4, MQTTSN_PUBREC, msg_id_rcv), (GW_IP, GW_PORT))

            elif msgType == MQTTSN_PUBREL:
                msg_id_rel = struct.unpack(">H", data[2:4])[0]
                sock.sendto(struct.pack(">BBH", 4, MQTTSN_PUBCOMP, msg_id_rel), (GW_IP, GW_PORT))
            
            elif msgType == MQTTSN_PINGRESP:
                last_ping = time.time()

if __name__ == "__main__":
    mqttsn_subscriber()