#!/usr/bin/env python3
# sub.py — MQTT-SN subscriber com SECSN + XOR (compatível com pub.py)

import socket
import struct
import random
import time
import sys

# =============================================================================
# 1. Constantes do protocolo
# =============================================================================

# MQTT-SN message types
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

# QoS levels
QOS_0 = 0b00
QOS_1 = 0b01
QOS_2 = 0b10

# SECSN (valores que você informou)
TYPE_SECSN = 0x3F7A
SECRET_KEY_SECSN = 0xA5C3F27B
SECRET_MASK_DATA_SECSN = int(
    "B37A94C4E18F2761A5F9C0B48D37ACD2E0B3C4D15A7F823BE6A2FDFE41C967A0F2E37B5C1DA4EF092B8D5C67A93F04D1B7E2C8A59431DE0A87B1F2C49E03D56A",
    16,
)

# Endereços
GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.4"

# =============================================================================
# 2. Funções SECSN
# =============================================================================

def ip_to_int(ip_addr):
    return struct.unpack(">I", socket.inet_aton(ip_addr))[0]

def generate_auth_authX(src_ip, dst_ip, src_port, dst_port, msg_type, secret_key=SECRET_KEY_SECSN):
    src_ip_int = ip_to_int(src_ip) & 0xFFFFFFFF
    dst_ip_int = ip_to_int(dst_ip) & 0xFFFFFFFF
    src_port &= 0xFFFF
    dst_port &= 0xFFFF
    msg_type &= 0xFF
    secret_key &= 0xFFFFFFFF

    op1 = (((src_ip_int & 0xFFFF) ^ (dst_ip_int >> 16)) + src_port) & 0xFFFF
    op2 = (((dst_port ^ msg_type) << 2) + (secret_key & 0xFFFF)) & 0xFFFF

    h = 0
    h = (h ^ src_ip_int) & 0xFFFFFFFF
    h = (((h << 5) | (h >> 27)) & 0xFFFFFFFF)
    h = (h + dst_ip_int) & 0xFFFFFFFF
    h = (h ^ (((src_port << 16) | dst_port) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h + ((msg_type << 8) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h ^ (((op1 << 16) | op2) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = (h + secret_key) & 0xFFFFFFFF

    return h & 0xFFFF

def build_secsn_packet(mqttsn_payload, src_port):
    """
    Prepend SECSN header (TYPE_SECSN, authX) to mqttsn_payload.
    authX computed with local src_port (important).
    """
    msg_type = mqttsn_payload[1]
    authX = generate_auth_authX(CLIENT_IP, GW_IP, src_port, GW_PORT, msg_type)
    secsn_header = struct.pack(">HH", TYPE_SECSN, authX)
    return secsn_header + mqttsn_payload

def xor_data(data_bytes, mask_int):
    """
    Same mask function used in pub client: expand mask_int to 64 bytes and xor.
    """
    mask_bytes = mask_int.to_bytes(64, "big")
    return bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])

# =============================================================================
# 3. Funções MQTT-SN básicas (constroem payload MQTT-SN, depois chamam build_secsn_packet)
# =============================================================================

def build_connect(src_port, client_id=None, duration=60):
    flags = 0x04  # CleanSession = 1
    protocol_id = 0x01
    if client_id is None:
        client_id = f"sub_client_{random.randint(1000,9999)}".encode()
    payload = struct.pack(">BBH", flags, protocol_id, duration) + client_id
    length = len(payload) + 2
    mqttsn_packet = struct.pack(">BB", length, MQTTSN_CONNECT) + payload
    return build_secsn_packet(mqttsn_packet, src_port)

def build_subscribe(topic_name, msg_id, qos_level, src_port):
    # TopicName variant (bit7=1), QoS bits in bits 5-6
    flags = (1 << 7) | (qos_level << 5)
    payload = struct.pack(">BH", flags, msg_id) + topic_name.encode("utf-8")
    length = len(payload) + 2
    mqttsn_packet = struct.pack(">BB", length, MQTTSN_SUBSCRIBE) + payload
    return build_secsn_packet(mqttsn_packet, src_port)

def build_unsubscribe_by_topicid(topic_id, msg_id, src_port):
    # TopicId
    # For UNSUBSCRIBE with TopicId, payload is: Flags(1), MsgId(2), TopicId(2)
    flags = 0x00  # TopicId type = 00
    payload = struct.pack(">BHH", flags, msg_id, topic_id)
    length = len(payload) + 2
    mqttsn_packet = struct.pack(">BB", length, MQTTSN_UNSUBSCRIBE) + payload
    return build_secsn_packet(mqttsn_packet, src_port)

def build_disconnect(src_port):
    mqttsn_packet = struct.pack(">BB", 2, MQTTSN_DISCONNECT)
    return build_secsn_packet(mqttsn_packet, src_port)

def build_puback(topic_id, msg_id, src_port):
    payload = struct.pack(">HHB", topic_id, msg_id, 0x00)
    length = len(payload) + 2
    mqttsn_packet = struct.pack(">BB", length, MQTTSN_PUBACK) + payload
    return build_secsn_packet(mqttsn_packet, src_port)

def build_pubrec(msg_id, src_port):
    mqttsn_packet = struct.pack(">BBH", 4, MQTTSN_PUBREC, msg_id)
    return build_secsn_packet(mqttsn_packet, src_port)

def build_pubrel(msg_id, src_port):
    mqttsn_packet = struct.pack(">BBH", 4, MQTTSN_PUBREL, msg_id)
    return build_secsn_packet(mqttsn_packet, src_port)

def build_pubcomp(msg_id, src_port):
    mqttsn_packet = struct.pack(">BBH", 4, MQTTSN_PUBCOMP, msg_id)
    return build_secsn_packet(mqttsn_packet, src_port)

# =============================================================================
# 4. Subscriber MQTT-SN com SECSN e desconexão limpa
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

    # --- CONNECT ---
    pkt = build_connect(local_port)
    sock.sendto(pkt, (GW_IP, GW_PORT))
    print("-> CONNECT (SECSN) enviado")

    # aguarda CONNACK (com SECSN)
    connack_received = False
    while not connack_received:
        try:
            data, _ = sock.recvfrom(4096)
            # parse SECSN header
            if len(data) < 4:
                continue
            secsn_type, authX = struct.unpack(">HH", data[:4])
            mqttsn = data[4:]
            if len(mqttsn) < 2:
                continue
            length, msgType = struct.unpack(">BB", mqttsn[:2])
            if msgType == MQTTSN_CONNACK:
                print("<- CONNACK recebido")
                connack_received = True
        except socket.timeout:
            continue

    # --- SUBSCRIBE ---
    msg_id = random.randint(1, 2000)
    sock.sendto(build_subscribe(topic, msg_id, qos_level, local_port), (GW_IP, GW_PORT))
    print(f"-> SUBSCRIBE (SECSN) enviado ({topic}, QoS={qos_choice})")

    # aguarda SUBACK e captura topic_id
    topic_id = None
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            if len(data) < 4:
                continue
            secsn_type, authX = struct.unpack(">HH", data[:4])
            mqttsn = data[4:]
            if len(mqttsn) < 2:
                continue
            length, msgType = struct.unpack(">BB", mqttsn[:2])
            if msgType == MQTTSN_SUBACK:
                # SUBACK payload: Flags(1), TopicId(2), MsgId(2), ReturnCode(1)
                flags = mqttsn[2]
                topic_id = struct.unpack(">H", mqttsn[3:5])[0]
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

            if len(data) < 4:
                continue
            secsn_type, authX = struct.unpack(">HH", data[:4])
            mqttsn = data[4:]
            if len(mqttsn) < 2:
                continue

            length, msgType = struct.unpack(">BB", mqttsn[:2])

            # PUBLISH
            if msgType == MQTTSN_PUBLISH:
                # mqttsn offsets: 0:length,1:msgType,2:flags,3-4:topicId,5-6:msgId,7:...payload
                flags = mqttsn[2]
                qos_bits = (flags >> 5) & 0x03
                topic_id_rcv = struct.unpack(">H", mqttsn[3:5])[0]
                msg_id_rcv = struct.unpack(">H", mqttsn[5:7])[0] if qos_bits != QOS_2 + 1 else 0  # safe default
                raw_payload = mqttsn[7:]
                # decodifica com a mesma máscara
                decoded_bytes = xor_data(raw_payload, SECRET_MASK_DATA_SECSN)
                payload = decoded_bytes.decode("utf-8", errors="ignore").rstrip("*")

                print(f"<- PUBLISH recebido: TopicID={topic_id_rcv}, QoS={qos_bits}, MsgID={msg_id_rcv}")
                print(f"   Conteúdo decodificado: '{payload}'")

                # respostas por QoS
                if qos_bits == QOS_1:
                    sock.sendto(build_puback(topic_id_rcv, msg_id_rcv, local_port), (GW_IP, GW_PORT))
                    print("-> PUBACK (SECSN) enviado\n")
                elif qos_bits == QOS_2:
                    sock.sendto(build_pubrec(msg_id_rcv, local_port), (GW_IP, GW_PORT))
                    print("-> PUBREC (SECSN) enviado\n")

            # PUBREL (broker -> subscriber, QoS 2 flow)
            elif msgType == MQTTSN_PUBREL:
                if len(mqttsn) >= 4:
                    msg_id = struct.unpack(">H", mqttsn[2:4])[0]
                else:
                    msg_id = 0
                sock.sendto(build_pubcomp(msg_id, local_port), (GW_IP, GW_PORT))
                print(f"-> PUBCOMP (SECSN) enviado (MsgID={msg_id})\n")

            # UNSUBACK
            elif msgType == MQTTSN_UNSUBACK:
                print("<- UNSUBACK recebido")

            # PINGRESP
            elif msgType == MQTTSN_PINGRESP:
                print("<- PINGRESP recebido")

            # DISCONNECT from gateway
            elif msgType == MQTTSN_DISCONNECT:
                print("<- DISCONNECT recebido do gateway")
                break

    except KeyboardInterrupt:
        print("\nEncerrando subscriber...")

        # --- UNSUBSCRIBE usando topic_id obtido do SUBACK ---
        if topic_id is not None:
            unsub_msgid = random.randint(2001, 3000)
            sock.sendto(build_unsubscribe_by_topicid(topic_id, unsub_msgid, local_port), (GW_IP, GW_PORT))
            print("-> UNSUBSCRIBE (SECSN, topicId) enviado")
            # aguarda UNSUBACK
            start = time.time()
            while time.time() - start < 5:
                try:
                    data, _ = sock.recvfrom(4096)
                    if len(data) < 4:
                        continue
                    mqttsn = data[4:]
                    if len(mqttsn) >= 2 and mqttsn[1] == MQTTSN_UNSUBACK:
                        print("<- UNSUBACK recebido")
                        break
                except socket.timeout:
                    continue
        else:
            print("Topic ID desconhecido — enviando UNSUBSCRIBE por nome (fallback).")
            sock.sendto(build_subscribe(topic, random.randint(3001,4000), qos_level, local_port), (GW_IP, GW_PORT))

        # --- DISCONNECT ---
        sock.sendto(build_disconnect(local_port), (GW_IP, GW_PORT))
        print("-> DISCONNECT (SECSN) enviado")
        # aguarda DISCONNECT do gateway
        start = time.time()
        while time.time() - start < 5:
            try:
                data, _ = sock.recvfrom(4096)
                if len(data) < 4:
                    continue
                mqttsn = data[4:]
                if len(mqttsn) >= 2 and mqttsn[1] == MQTTSN_DISCONNECT:
                    print("<- DISCONNECT recebido. Finalizando...\n")
                    break
            except socket.timeout:
                continue

        sock.close()
        sys.exit(0)


# =============================================================================
# Execução Principal
# =============================================================================

if __name__ == "__main__":
    mqttsn_subscriber()
