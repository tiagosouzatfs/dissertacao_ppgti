import socket
import struct
import random
import time

# Configurações de Rede
GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
PREDEFINED_TOPIC_ID = 10
TIMEOUT = 5.0

# Constantes MQTT-SN
MQTTSN_CONNECT, MQTTSN_DISCONNECT = 0x04, 0x18
MQTTSN_PUBLISH = 0x0C
QOS_M1, QOS_0 = 0b11, 0b00
TOPICIDTYPE_PREDEFINED = 0b01
SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

# --- Funções de Criptografia ---
def generate_otp(salt):
    otp = ((salt << 7) & 0xFFFF) ^ (salt >> 9) ^ 0xA5A5
    otp = ((otp << 3) & 0xFFFF) | (otp >> 13)
    return otp & 0xFFFF

def otp_encrypt_topic(topic_id, salt):
    otp = generate_otp(salt)
    val = (topic_id ^ SECRET_TOPIC_ID ^ otp) & 0xFFFF
    return ((val << 4) | (val >> 12)) & 0xFFFF

def otp_process_data(data):
    payload_salt = random.getrandbits(16)
    otp = generate_otp(payload_salt)

    if isinstance(data, str):
        data_bytes = data.encode().ljust(62, b"*")[:62]
    else:
        data_bytes = data.ljust(62, b"*")[:62]
        
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, 'big')
    output = [b ^ (mask_bytes[i%64] ^ (otp & 0xFF if i%2==0 else (otp>>8)&0xFF)) for i, b in enumerate(data_bytes)]
    return struct.pack('>H', payload_salt) + bytes(output)

# Lógica de Publicação
def run_benchmark_p4ssn(msgs_per_qos):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))
    sock.settimeout(TIMEOUT)
    
    # QoS -1 (Disparo Direto)
    print(f"Iniciando msgs QoS -1...")
    payload_m1 = b"P4SSN_DATA_BENCHMARK" + f"_{time.time()}".encode()
    
    for i in range(msgs_per_qos):
        salt = random.randint(1, 0xFFFF)
        flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
        # Header padrão: Length(1), Type(1), Flags(1), TopicId(2), MsgId(2) = 7 bytes
        t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt)
        encrypted_payload = otp_process_data(payload_m1)
        
        header = struct.pack('>BB BHH', len(encrypted_payload)+7, MQTTSN_PUBLISH, flags, t_enc, salt)
        sock.sendto(header + encrypted_payload, (GW_IP, GW_PORT))

        time.sleep(0.0005)

    time.sleep(0.001)

    # QoS 0 (Connect -> Publish -> Disconnect)
    print("Iniciando msgs QoS 0 (Fluxo Completo)...")
    payload_q0 = b"P4SSN_DATA_BENCHMARK" + f"_{time.time()}".encode()
    
    for i in range(msgs_per_qos):
        try:
            # CONNECT
            client_id = f"p4ssn_client_{i}"
            conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
            sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera CONNACK

            time.sleep(0.0005)

            # PUBLISH
            salt = random.randint(1, 0xFFFF)
            flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED 
            t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt)
            encrypted_payload = otp_process_data(payload_q0)
            header = struct.pack('>BB BHH', len(encrypted_payload)+7, MQTTSN_PUBLISH, flags, t_enc, salt)
            sock.sendto(header + encrypted_payload, (GW_IP, GW_PORT))

            time.sleep(0.0005)

            # DISCONNECT
            sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera DISCONNECT

            time.sleep(0.0005)

        except Exception as e:
            print(f"Erro: {e}")

    sock.close()

if __name__ == "__main__":

    # Testes Gerais
    MSGS_POR_QOS = 500 # 500 QoS -1 + 500 QoS 0 = 1k total
    # MSGS_POR_QOS = 2500 # 2.500 QoS -1 + 2.500 QoS 0 = 5k total
    # MSGS_POR_QOS = 5000 # 5.000 QoS -1 + 5.000 QoS 0 = 10k total

    print(f"--- INICIANDO BENCHMARK P4SSN ---")

    run_benchmark_p4ssn(MSGS_POR_QOS)

    print("\n[SUCESSO] BENCHMARK P4SSN finalizado.")