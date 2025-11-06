import socket
import struct
import time

# =============================================================================
# 1. Definição das Constantes e Estruturas do Protocolo
# =============================================================================

# Constantes MQTT-SN
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

# Constantes SECSN (do código P4)
TYPE_SECSN = 0x3F7A
SECRET_KEY_SECSN = 0xA5C3F27B
SECRET_MASK_DATA_SECSN = 0xB37A94C4E18F2761A5F9C0B48D37ACD2E0B3C4D15A7F823BE6A2FDFE41C967A0F2E37B5C1DA4EF092B8D5C67A93F04D1B7E2C8A59431DE0A87B1F2C49E03D56A

# QoS Levels
QOS_M1 = 0b11 # -1
QOS_0 = 0b00
QOS_1 = 0b01
QOS_2 = 0b10

# Topic ID Types
TOPICIDTYPE_TOPICNAME = 0b00
TOPICIDTYPE_PREDEFINEDTOPIC = 0b01
TOPICIDTYPE_SHORTTOPICNAME = 0b10

# Endereços de Rede (Fornecidos pelo Usuário)
GW_IP = "10.0.0.2"
GW_PORT = 1884
CLIENT_IP = "10.0.0.3"
CLIENT_PORT = 46572 # Porta de origem definida

SERVER_ADDRESS = (GW_IP, GW_PORT)

# Conversão de IP para inteiro (Big Endian)
def ip_to_int(ip_addr):
    return struct.unpack('>I', socket.inet_aton(ip_addr))[0]

CLIENT_IP_INT = ip_to_int(CLIENT_IP)
GW_IP_INT = ip_to_int(GW_IP)

# =============================================================================
# 2. Funções Auxiliares
# =============================================================================

# ======================================================
# === SECSN AUTHX (compatível com P4) ==========
# ======================================================
def generate_auth_authX(src_ip, dst_ip, src_port, dst_port, msg_type, secret_key=SECRET_KEY_SECSN):
    def ip_to_int(ip):
        # Esta função interna é redundante se chamada aqui, mas mantida para clareza
        return struct.unpack("!I", bytes(map(int, ip.split('.'))))[0]

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

def build_secsn_packet(mqttsn_payload):
    """Constrói o pacote SECSN + MQTT-SN."""
    
    if len(mqttsn_payload) < 2:
        raise ValueError("Payload MQTT-SN muito curto.")
    
    msg_type = mqttsn_payload[1] # O segundo byte é o MsgType
    
    authX = generate_auth_authX(CLIENT_IP, GW_IP, CLIENT_PORT, GW_PORT, msg_type)
    
    # Monta o Header SECSN: msgSecType (H) + authX (H)
    secsn_header = struct.pack('>HH', TYPE_SECSN, authX)
    
    return secsn_header + mqttsn_payload

def send_and_receive(sock, packet, expected_msg_type=None, timeout=5):
    """Envia o pacote e espera pela resposta, se esperado."""
    
    sock.sendto(packet, SERVER_ADDRESS)
    
    sock.settimeout(timeout)
    try:
        data, server = sock.recvfrom(1024)
        
        if len(data) < 4:
            print("<- ERRO: Resposta muito curta para conter o header SECSN.")
            return None
            
        # Desempacota o Header SECSN
        msgSecType, authx = struct.unpack('>HH', data[:4])
        
        if msgSecType != TYPE_SECSN:
            print(f"<- ERRO: Tipo de segurança inesperado: {hex(msgSecType)}. Esperado: {hex(TYPE_SECSN)}")
            return None
            
        mqttsn_payload = data[4:]
        
        if len(mqttsn_payload) < 2:
            print("<- ERRO: Payload MQTT-SN muito curto para conter o Fixed Header.")
            return None
            
        # Desempacota o Fixed Header MQTT-SN
        length, msgType = struct.unpack('>BB', mqttsn_payload[:2])
        
        if expected_msg_type is not None and msgType != expected_msg_type:
            print(f"<- ERRO: Recebido tipo {hex(msgType)} inesperado. Esperado: {hex(expected_msg_type)}")
            return None
            
        print(f"<- Recebido: Tipo {hex(msgType)}")
        return mqttsn_payload
        
    except socket.timeout:
        print("<- ERRO: Timeout na espera pela resposta.")
        return None
    except Exception as e:
        print(f"<- ERRO ao receber/desempacotar: {e}")
        return None

# =============================================================================
# 3. Funções de Construção de Pacotes MQTT-SN (Sem alterações)
# =============================================================================

def xor_data(data_str, mask_int):
    data_bytes = data_str.encode("utf-8")
    mask_bytes = mask_int.to_bytes(64, 'big')  # 512 bits = 64 bytes
    masked = bytes([b ^ mask_bytes[i % len(mask_bytes)] for i, b in enumerate(data_bytes)])
    return masked

def build_connect(client_id="struct_client", duration=60):
    flags = 0x02
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode('utf-8')
    length = len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_CONNECT) + payload
    return build_secsn_packet(mqttsn_packet)

def build_register(topic_name, msg_id):
    topic_id = 0x0000
    payload = struct.pack('>HH', topic_id, msg_id) + topic_name.encode('utf-8')
    length = len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_REGISTER) + payload
    return build_secsn_packet(mqttsn_packet)

def build_publish(qos_level, topic_identifier, msg_id, data):
    # Determina tipo de Topic e payload
    if isinstance(topic_identifier, str):
        if len(topic_identifier) == 2:
            topic_id_type = TOPICIDTYPE_SHORTTOPICNAME
            topic_id_payload = topic_identifier.encode('utf-8')
            topic_name_payload = b''
        else:
            topic_id_type = TOPICIDTYPE_TOPICNAME
            topic_id_payload = struct.pack('>H', 0x0000)  # Topic ID será 0, mas o name vem no payload
            topic_name_payload = topic_identifier.encode('utf-8')
    elif isinstance(topic_identifier, int):
        topic_id_type = TOPICIDTYPE_PREDEFINEDTOPIC
        topic_id_payload = struct.pack('>H', topic_identifier)
        topic_name_payload = b''
    else:
        raise TypeError("topic_identifier deve ser string ou inteiro")

    flags = (qos_level << 5) | (topic_id_type << 2)
    
    # Msg ID só existe se QoS != -1
    fixed_header = struct.pack('>B', flags) + topic_id_payload
    if qos_level != QOS_M1:
        fixed_header += struct.pack('>H', msg_id)
    
    # Payload variável
    if isinstance(data, str):
        data = data.encode('utf-8')
    variable_payload = data + topic_name_payload
    
    payload = fixed_header + variable_payload
    length = len(payload) + 2  # Incluindo Length + MsgType
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_PUBLISH) + payload
    
    return build_secsn_packet(mqttsn_packet)

def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    length = len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_PUBREL) + payload
    return build_secsn_packet(mqttsn_packet)

def build_disconnect():
    payload = b''
    length = len(payload) + 2
    mqttsn_packet = struct.pack('>BB', length, MQTTSN_DISCONNECT) + payload
    return build_secsn_packet(mqttsn_packet)

# =============================================================================
# 4. Funções de Sequência de Mensagens (Sem alterações)
# =============================================================================

def sequence_qos_minus1(sock, topic_identifier="sh", msg_id=0x0001, data="QoS -1 Message"):
    print("\n--- Sequência QoS -1 (Apenas PUBLISH - Short Topic Name) ---")
    
    data = xor_data(data, SECRET_MASK_DATA_SECSN)

    publish_packet = build_publish(QOS_M1, topic_identifier, msg_id, data)
    
    print(f"-> Enviando: PUBLISH (QoS -1) para tópico '{topic_identifier}'")
    sock.sendto(publish_packet, SERVER_ADDRESS)
    print("Mensagem PUBLISH (QoS -1) enviada.")

def sequence_qos_0(sock, topic_name="test/qos0/topic", msg_id=0x0001, data="QoS 0 Message"):
    print("\n--- Sequência QoS 0 (Topic ID - REGISTER/PUBLISH) ---")
    
    data = xor_data(data, SECRET_MASK_DATA_SECSN)

    # 1. CONNECT
    connect_packet = build_connect()
    connack_response = send_and_receive(sock, connect_packet, expected_msg_type=MQTTSN_CONNACK)
    if connack_response is None: return

    # 2. REGISTER
    register_packet = build_register(topic_name, msg_id)
    regack_response = send_and_receive(sock, register_packet, expected_msg_type=MQTTSN_REGACK)
    if regack_response is None: return
    
    registered_topic_id = struct.unpack('>H', regack_response[2:4])[0]
    print(f"Topic ID registrado: {registered_topic_id}")

    # 3. PUBLISH (QoS 0)
    publish_packet = build_publish(QOS_0, registered_topic_id, msg_id, data)
    
    print(f"-> Enviando: PUBLISH (QoS 0) com Topic ID {registered_topic_id}")
    sock.sendto(publish_packet, SERVER_ADDRESS)
    print("Mensagem PUBLISH (QoS 0) enviada.")

    # 4. DISCONNECT
    disconnect_packet = build_disconnect()
    send_and_receive(sock, disconnect_packet, expected_msg_type=MQTTSN_DISCONNECT)

def sequence_qos_1(sock, topic_name="test/qos1/topic", msg_id=0x0002, data="QoS 1 Message"):
    print("\n--- Sequência QoS 1 (Topic Name - PUBLISH) ---")
    
    data = xor_data(data, SECRET_MASK_DATA_SECSN)

    # 1. CONNECT
    connect_packet = build_connect()
    connack_response = send_and_receive(sock, connect_packet, expected_msg_type=MQTTSN_CONNACK)
    if connack_response is None: return

    # 2. REGISTER
    register_packet = build_register(topic_name, msg_id)
    regack_response = send_and_receive(sock, register_packet, expected_msg_type=MQTTSN_REGACK)
    if regack_response is None: return
    
    registered_topic_id = struct.unpack('>H', regack_response[2:4])[0]
    print(f"Topic ID registrado: {registered_topic_id}")

    # 3. PUBLISH (QoS 1)
    publish_packet = build_publish(QOS_1, topic_name, msg_id, data)
    
    # Envia e espera pelo PUBACK
    puback_response = send_and_receive(sock, publish_packet, expected_msg_type=MQTTSN_PUBACK)
    if puback_response is None: return

    # 4. DISCONNECT
    disconnect_packet = build_disconnect()
    send_and_receive(sock, disconnect_packet, expected_msg_type=MQTTSN_DISCONNECT)

def sequence_qos_2(sock, topic_name="test/qos2/topic", msg_id=0x0003, data="QoS 2 Message"):
    print("\n--- Sequência QoS 2 (Topic ID - REGISTER/PUBLISH) ---")
    
    data = xor_data(data, SECRET_MASK_DATA_SECSN)

    # 1. CONNECT
    connect_packet = build_connect()
    connack_response = send_and_receive(sock, connect_packet, expected_msg_type=MQTTSN_CONNACK)
    if connack_response is None: return

    # 2. REGISTER
    register_packet = build_register(topic_name, msg_id)
    regack_response = send_and_receive(sock, register_packet, expected_msg_type=MQTTSN_REGACK)
    if regack_response is None: return
    
    registered_topic_id = struct.unpack('>H', regack_response[2:4])[0]
    print(f"Topic ID registrado: {registered_topic_id}")

    # 3. PUBLISH (QoS 2)
    publish_packet = build_publish(QOS_2, registered_topic_id, msg_id, data)
    
    # Envia e espera pelo PUBREC
    pubrec_response = send_and_receive(sock, publish_packet, expected_msg_type=MQTTSN_PUBREC)
    if pubrec_response is None: return
    
    # 4. PUBREL
    pubrel_packet = build_pubrel(msg_id)
    
    # Envia e espera pelo PUBCOMP
    pubcomp_response = send_and_receive(sock, pubrel_packet, expected_msg_type=MQTTSN_PUBCOMP)
    if pubcomp_response is None: return

    # 5. DISCONNECT
    disconnect_packet = build_disconnect()
    send_and_receive(sock, disconnect_packet, expected_msg_type=MQTTSN_DISCONNECT)

# =============================================================================
# 5. Execução Principal (Modificada)
# =============================================================================

if __name__ == "__main__":
    # Cria um socket UDP e o associa à porta de origem definida
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Associa o socket à porta e IP de origem
        sock.bind((CLIENT_IP, CLIENT_PORT))
    except OSError as e:
        print(f"ERRO: Não foi possível associar o socket ao IP/Porta de origem ({CLIENT_IP}:{CLIENT_PORT}).")
        print("Certifique-se de que o IP de origem está correto e a porta está livre.")
        print(f"Detalhes do erro: {e}")
        sock.close()
        exit(1)
    
    print(f"Cliente MQTT-SN iniciado em {CLIENT_IP}:{CLIENT_PORT}")
    print(f"Gateway MQTT-SN em {GW_IP}:{GW_PORT}")
    
    # --- Lógica de seleção por QoS ---
    sequences = {
        "-1": sequence_qos_minus1,
        "0": sequence_qos_0,
        "1": sequence_qos_1,
        "2": sequence_qos_2
    }
    
    print("\n--- Escolha a sequência MQTT-SN a ser executada ---")
    qos_choice = input("Digite o nível de QoS (-1, 0, 1, 2): ")
    selected_sequence = sequences.get(qos_choice)

    if not selected_sequence:
        print("\nERRO: Escolha de QoS inválida. Por favor, digite -1, 0, 1 ou 2.")
        sock.close()
        exit(1)

    # --- Entrada e validação do campo 'data' ---
    while True:
        data_msg = input("Digite o conteúdo da mensagem PUBLISH (máx 64 bytes): ")
        data_len = len(data_msg.encode("utf-8"))

        if data_len > 64:
            print(f"ERRO: A mensagem tem {data_len} bytes ({data_len - 64} bytes acima do limite). Redigite.")
            continue
        elif data_msg.endswith("."):
            print("ERRO: O último caractere não pode ser '.', pois é um limitador de mensagem no P4SSN. Redigite.")
            continue
        elif data_len < 64:
            data_msg = data_msg.ljust(64, ".")
            #print(f"A mensagem foi completada com '.' até 64 bytes.")
        break

    print(f"\n--- Iniciando sequência para QoS {qos_choice} ---")
    selected_sequence(sock, data=data_msg)

    sock.close()
    print("\n--- Fim da execução do cliente Struct ---")
