import socket
import struct
import random
import time
from multiprocessing import Process

# --- Configurações de Rede ---
GW_IP, GW_PORT = "10.0.0.1", 1884
CLIENT_IP = "10.0.0.2"
PREDEFINED_TOPIC_ID = 10
TIMEOUT = 5.0

# --- Constantes P4SSN / MQTT-SN ---
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

def otp_process_data(data_str, salt):
    payload_salt = random.getrandbits(16)
    otp = generate_otp(payload_salt)
    data_bytes = data_str.encode().ljust(62, b"*")[:62]
    mask_bytes = SECRET_DATA_PUBLISH.to_bytes(64, 'big')
    output = [b ^ (mask_bytes[i%64] ^ (otp & 0xFF if i%2==0 else (otp>>8)&0xFF)) for i, b in enumerate(data_bytes)]
    return struct.pack('>H', payload_salt) + bytes(output)

# --- Lógica de Disparo ---
def run_stress_client(worker_id, msgs_per_qos):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((CLIENT_IP, 0))
    sock.settimeout(TIMEOUT)
    
    # 1. Bateria QoS -1 (Disparo Direto)
    print(f"[Worker {worker_id}] Iniciando msgs QoS -1...")
    for i in range(msgs_per_qos):
        salt = random.randint(1, 0xFFFF)
        flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
        t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt)
        p_enc = otp_process_data("P4SSN_STRESS_M1", salt)
        header = struct.pack('>BB BHH', len(p_enc)+7, MQTTSN_PUBLISH, flags, t_enc, salt)
        sock.sendto(header + p_enc, (GW_IP, GW_PORT))
        time.sleep(0.0005)

    # 2. Bateria QoS 0 (Connect -> Publish -> Disconnect)
    print(f"[Worker {worker_id}] Iniciando msgs QoS 0 (Fluxo Completo)...")
    for i in range(msgs_per_qos):
        try:
            # CONNECT
            client_id = f"w{worker_id}_i{i}"
            conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
            sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
            sock.recvfrom(1024) # Espera CONNACK

            # PUBLISH
            salt = random.randint(1, 0xFFFF)
            flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED # Retain 0
            t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt)
            p_enc = otp_process_data("P4SSN_STRESS_Q0", salt)
            header = struct.pack('>BB BHH', len(p_enc)+7, MQTTSN_PUBLISH, flags, t_enc, salt)
            sock.sendto(header + p_enc, (GW_IP, GW_PORT))

            # DISCONNECT
            sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
            time.sleep(0.001)
        except:
            pass

    sock.close()

if __name__ == "__main__":
    NUM_CLIENTES = 4
    MSGS_POR_QOS = 10000 # 10k QoS -1 + 10k QoS 0 = 20k por cliente (80k total)
    
    processos = []
    print(f"--- INICIANDO BENCHMARK MQTTSN PADRÃO: 80.000 MENSAGENS ---")
    
    for i in range(NUM_CLIENTES):
        p = Process(target=run_stress_client, args=(i, MSGS_POR_QOS))
        processos.append(p)
        p.start()

    for p in processos:
        p.join()

    print("\n[SUCESSO] Teste de estresse finalizado.")