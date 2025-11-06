#!/usr/bin/env python3
import socket
import struct
import random
import time

# =============================================================================
# Constantes
# =============================================================================

MQTTSN_CONNECT = 0x04
MQTTSN_CONNACK = 0x05
MQTTSN_REGISTER = 0x0A
MQTTSN_REGACK = 0x0B
MQTTSN_PUBLISH = 0x0C
MQTTSN_PUBACK = 0x0D
MQTTSN_PUBREC = 0x0F
MQTTSN_PUBREL = 0x10
MQTTSN_PUBCOMP = 0x0E
MQTTSN_DISCONNECT = 0x18

TYPE_SECSN = 0x3F7A
SECRET_KEY_SECSN = 0xA5C3F27B
SECRET_MASK_DATA_SECSN = 0xB37A94C4E18F2761A5F9C0B48D37ACD2E0B3C4D15A7F823BE6A2FDFE41C967A0F2E37B5C1DA4EF092B8D5C67A93F04D1B7E2C8A59431DE0A87B1F2C49E03D56A

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10

TOPICIDTYPE_NORMAL = 0b00

GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.3"

SERVER_ADDRESS = (GW_IP, GW_PORT)

# dynamic source port (set after bind)
SRC_PORT = None

# =============================================================================
# Funções auxiliares
# =============================================================================

def ip_to_int(ip_addr):
    return struct.unpack('>I', socket.inet_aton(ip_addr))[0]

def generate_auth_authX(src_ip, dst_ip, src_port, dst_port, msg_type, secret_key=SECRET_KEY_SECSN):
    def ip_to_int_local(ip):
        return struct.unpack("!I", bytes(map(int, ip.split('.'))))[0]
    src_ip_int = ip_to_int_local(src_ip) & 0xFFFFFFFF
    dst_ip_int = ip_to_int_local(dst_ip) & 0xFFFFFFFF
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

def build_secsn_packet(mqttsn_payload):
    """Constroi header SECSN usando a porta de origem real (SRC_PORT)."""
    global SRC_PORT
    if SRC_PORT is None:
        # fallback (não esperado)
        src_port = 0
    else:
        src_port = SRC_PORT
    msg_type = mqttsn_payload[1]
    authX = generate_auth_authX(CLIENT_IP, GW_IP, src_port, GW_PORT, msg_type)
    secsn_header = struct.pack('>HH', TYPE_SECSN, authX)
    return secsn_header + mqttsn_payload

def send_and_receive(sock, packet, expected_msg_type=None, timeout=5):
    sock.sendto(packet, SERVER_ADDRESS)
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
        msgSecType, authX = struct.unpack('>HH', data[:4])
        mqttsn_payload = data[4:]
        if len(mqttsn_payload) < 2:
            print("<- ERRO: payload MQTT-SN muito curto")
            return None
        length, msgType = struct.unpack('>BB', mqttsn_payload[:2])
        print(f"<- Recebido: Tipo {hex(msgType)} (len={length})")
        if expected_msg_type and msgType != expected_msg_type:
            print(f"   [WARN] recebido {hex(msgType)} != esperado {hex(expected_msg_type)}")
            return None
        return mqttsn_payload
    except socket.timeout:
        print("<- ERRO: Timeout na resposta.")
        return None

def recv_only(sock, expected_msg_type=None, timeout=5):
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
        msgSecType, authX = struct.unpack('>HH', data[:4])
        mqttsn_payload = data[4:]
        if len(mqttsn_payload) < 2:
            print("Recebido payload MQTT-SN muito curto")
            return None
        length, msgType = struct.unpack('>BB', mqttsn_payload[:2])
        print(f"<- Recebido (recv_only): Tipo {hex(msgType)} (len={length})")
        if expected_msg_type and msgType != expected_msg_type:
            print(f"   [WARN] recebido {hex(msgType)} != esperado {hex(expected_msg_type)}")
            return None
        return mqttsn_payload
    except socket.timeout:
        print("<- ERRO: Timeout esperando mensagem.")
        return None

def xor_data(data_str, mask_int):
    data_bytes = data_str.encode("utf-8")
    mask_bytes = mask_int.to_bytes(64, 'big')
    return bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])

# =============================================================================
# Construção de pacotes MQTT-SN
# =============================================================================

def build_connect(client_id, duration=60):
    flags = 0x02
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode('utf-8')
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_CONNECT) + payload
    return build_secsn_packet(mqttsn_packet)

def build_register(topic_name, msg_id):
    topic_id = 0x0000
    payload = struct.pack('>HH', topic_id, msg_id) + topic_name.encode('utf-8')
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_REGISTER) + payload
    return build_secsn_packet(mqttsn_packet)

def build_publish(qos_level, topic_id, msg_id, data):
    """Monta publish garantindo topicId(2) + msgId(2). msgId=0 se QoS -1."""
    flags = ((qos_level & 0x03) << 5) | (TOPICIDTYPE_NORMAL & 0x03)
    msg_id_to_send = msg_id if qos_level != QOS_M1 else 0x0000
    header = struct.pack('>BHH', flags, topic_id, msg_id_to_send)
    payload = data if isinstance(data, (bytes, bytearray)) else data.encode('utf-8')
    length = len(header) + len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_PUBLISH) + header + payload
    final_packet = build_secsn_packet(mqttsn_packet)

    print("-> [DEBUG] PUBLISH montado:")
    print(f"   QoS bits: {qos_level:02b}")
    print(f"   flags: 0x{flags:02x}")
    print(f"   topic_id: 0x{topic_id:04x}")
    print(f"   msg_id_sent: 0x{msg_id_to_send:04x}")
    print(f"   mqtt-sn length field: {length}")
    print(f"   total bytes (com SECSN): {len(final_packet)}")

    return final_packet

def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    mqttsn_packet = struct.pack('>BB', len(payload) + 2, MQTTSN_PUBREL) + payload
    return build_secsn_packet(mqttsn_packet)

def build_disconnect():
    mqttsn_packet = struct.pack('>BB', 2, MQTTSN_DISCONNECT)
    return build_secsn_packet(mqttsn_packet)

# =============================================================================
# Sequência principal (com fluxos corretos QoS 1 e 2)
# =============================================================================

def sequence_common(sock, qos_level, msg_id, topic_name, data, client_id):
    data_bytes = xor_data(data, SECRET_MASK_DATA_SECSN)

    # CONNECT
    print(f"-> Enviando: CONNECT (client_id={client_id})")
    connect_packet = build_connect(client_id)
    if not send_and_receive(sock, connect_packet, MQTTSN_CONNACK):
        print("CONNECT falhou, abortando sequência.")
        return

    # REGISTER
    print("-> Enviando: REGISTER")
    register_packet = build_register(topic_name, msg_id)
    regack = send_and_receive(sock, register_packet, MQTTSN_REGACK)
    if not regack:
        print("REGISTER falhou, abortando sequência.")
        return

    topic_id = struct.unpack('>H', regack[2:4])[0]
    print(f"<- REGACK recebido: topic_id = {topic_id}")

    # PUBLISH
    publish_packet = build_publish(qos_level, topic_id, msg_id, data_bytes)
    print(f"-> Enviando: PUBLISH (QoS {qos_level})")
    sock.sendto(publish_packet, SERVER_ADDRESS)

    # Fluxos por QoS
    if qos_level == QOS_M1:
        print("QoS -1: sem confirmação.")
        # Disconnect
        disconnect_packet = build_disconnect()
        send_and_receive(sock, disconnect_packet, MQTTSN_DISCONNECT)
        return

    if qos_level == QOS_0:
        print("QoS 0: sem confirmação.")
        disconnect_packet = build_disconnect()
        send_and_receive(sock, disconnect_packet, MQTTSN_DISCONNECT)
        return

    if qos_level == QOS_1:
        print("Aguardando PUBACK...")
        puback = recv_only(sock, expected_msg_type=MQTTSN_PUBACK, timeout=5)
        if not puback:
            print("PUBACK não recebido (timeout).")
        else:
            print("PUBACK recebido.")
        disconnect_packet = build_disconnect()
        send_and_receive(sock, disconnect_packet, MQTTSN_DISCONNECT)
        return

    if qos_level == QOS_2:
        print("Aguardando PUBREC...")
        pubrec = recv_only(sock, expected_msg_type=MQTTSN_PUBREC, timeout=5)
        if not pubrec:
            print("PUBREC não recebido (timeout).")
            disconnect_packet = build_disconnect()
            send_and_receive(sock, disconnect_packet, MQTTSN_DISCONNECT)
            return
        print("PUBREC recebido. Enviando PUBREL...")
        pubrel_pkt = build_pubrel(msg_id)
        sock.sendto(pubrel_pkt, SERVER_ADDRESS)
        print("Aguardando PUBCOMP...")
        pubcomp = recv_only(sock, expected_msg_type=MQTTSN_PUBCOMP, timeout=5)
        if not pubcomp:
            print("PUBCOMP não recebido (timeout).")
        else:
            print("PUBCOMP recebido.")
        disconnect_packet = build_disconnect()
        send_and_receive(sock, disconnect_packet, MQTTSN_DISCONNECT)
        return

# =============================================================================
# Execução principal
# =============================================================================

if __name__ == "__main__":
    # Cria socket e usa porta ephemeral (0) para evitar conflitos de client_id no gateway
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))  # porta 0 -> OS escolhe porta livre
    # atualiza porta de origem global usada no SECSN
    SRC_PORT = sock.getsockname()[1]
    print(f"Socket ligado em {CLIENT_IP}:{SRC_PORT}")

    # Gera client_id aleatório para evitar conflitos de sessão
    client_id = f"struct_client_{random.randint(1000,9999)}"
    print(f"Usando client_id = {client_id}")

    sequences = {"-1": QOS_M1, "0": QOS_0, "1": QOS_1, "2": QOS_2}
    qos_choice = input("Digite o nível de QoS (-1, 0, 1, 2): ")
    qos_level = sequences.get(qos_choice)
    if qos_level is None:
        print("QoS inválido.")
        sock.close()
        exit(1)

    topic_name = input("Digite o tópico: ")

    while True:
        data_msg = input("Digite a mensagem (máx 64 bytes): ")
        data_len = len(data_msg.encode("utf-8"))
        if data_len > 64:
            print(f"ERRO: {data_len-64} bytes acima do limite de 64. Redigite.")
            continue
        elif data_msg.endswith("*"):
            print("ERRO: O último caractere não pode ser '*'. Redigite.")
            continue
        elif data_len < 64:
            data_msg = data_msg.ljust(64, "*")
        break

    sequence_common(sock, qos_level, 0x0001, topic_name, data_msg, client_id)

    sock.close()
    print("\n--- Fim da execução ---")
