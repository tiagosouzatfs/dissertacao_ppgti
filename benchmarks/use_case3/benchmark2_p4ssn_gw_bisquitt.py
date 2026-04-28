import socket
import struct
import random
import time

# Configurações de Rede
GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
PREDEFINED_TOPIC_ID = 20
TIMEOUT = 5.0

# Constantes MQTT-SN
MQTTSN_CONNECT, MQTTSN_DISCONNECT = 0x04, 0x18
MQTTSN_CONNACK = 0x05
MQTTSN_PUBLISH = 0x0C
QOS_M1, QOS_0 = 0b11, 0b00
TOPICIDTYPE_PREDEFINED = 0b01
SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

# --- Funções de Criptografia P4SSN ---
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
    test_qos = [QOS_M1, QOS_0]

    for current_qos in test_qos:
        label = "-1" if current_qos == QOS_M1 else "0"
        print(f"Iniciando benchmark P4SSN QoS {label}...")

        # --- CASO ESPECIAL: QoS -1 ---
        if current_qos == QOS_M1:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((CLIENT_IP, 0))
            sock.settimeout(TIMEOUT)
            
            try:
                # CONNECT com Keep Alive de 360 segundos
                client_id = f"p4ssn_m1_persistent_{random.randint(1000, 9999)}"
                conn = struct.pack('>BBH', 0x04, 0x01, 360) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                
                resp, _ = sock.recvfrom(1024)
                if resp[1] == MQTTSN_CONNACK:
                    print(f"   Sessão P4SSN QoS -1 estabelecida. Enviando {msgs_per_qos} msgs...")

                for i in range(msgs_per_qos):
                    payload = b"P4SSN_DATA_BENCHMARK" + f"_{i}_{time.time()}".encode()
                    
                    # No QoS -1, salt de cabeçalho pode ser 0x0000 ou randômico para diversificar o tópico
                    salt_header = random.randint(1, 0xFFFF) 
                    flags = (QOS_M1 << 5) | TOPICIDTYPE_PREDEFINED
                    
                    t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt_header)
                    encrypted_payload = otp_process_data(payload)
                    
                    header = struct.pack('>BB BHH', len(encrypted_payload) + 7, MQTTSN_PUBLISH, flags, t_enc, salt_header)
                    sock.sendto(header + encrypted_payload, (GW_IP, GW_PORT))
                    
                    # Delay mínimo para o BMv2 processar sem dropar por buffer
                    time.sleep(0.001)

                # DISCONNECT
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                sock.recvfrom(1024)
                print("   Sessão P4SSN QoS -1 encerrada com sucesso.")

            except Exception as e:
                print(f"Erro no benchmark persistente QoS -1: {e}")
            finally:
                sock.close()

        # --- CASO PADRÃO: QoS 0 (EFÊMERO - CONNECT/DISCONNECT POR MSG) ---
        else:
            for i in range(msgs_per_qos):
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((CLIENT_IP, 0))
                sock.settimeout(TIMEOUT)
                
                try:
                    payload = b"P4SSN_DATA_BENCHMARK" + f"_{i}_{time.time()}".encode()
                    client_id = f"p4ssn_client_0_{i}_{random.randint(1000, 9999)}"
                    
                    # CONNECT
                    conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                    sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                    
                    resp, _ = sock.recvfrom(1024)
                    if resp[1] != MQTTSN_CONNACK: raise Exception("CONNACK falhou")

                    time.sleep(0.001)

                    # PUBLISH (P4SSN)
                    salt_header = random.randint(1, 0xFFFF)
                    flags = (QOS_0 << 5) | TOPICIDTYPE_PREDEFINED
                    t_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt_header)
                    encrypted_payload = otp_process_data(payload)
                    
                    header = struct.pack('>BB BHH', len(encrypted_payload) + 7, MQTTSN_PUBLISH, flags, t_enc, salt_header)
                    sock.sendto(header + encrypted_payload, (GW_IP, GW_PORT))

                    time.sleep(0.001)

                    # DISCONNECT
                    sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))
                    sock.recvfrom(1024) # Espera DISCONNECT

                    time.sleep(0.001)

                except Exception as e:
                    print(f"Erro no loop QoS 0, msg {i}: {e}")
                finally:
                    sock.close()

if __name__ == "__main__":

    # Testes Gerais
    MSGS_POR_QOS = 500 # 500 QoS -1 + 500 QoS 0 = 1k total
    # MSGS_POR_QOS = 2500 # 2.500 QoS -1 + 2.500 QoS 0 = 5k total
    # MSGS_POR_QOS = 5000 # 5.000 QoS -1 + 5.000 QoS 0 = 10k total

    print(f"--- INICIANDO BENCHMARK P4SSN ---")

    run_benchmark_p4ssn(MSGS_POR_QOS)

    print("\n[SUCESSO] BENCHMARK P4SSN finalizado.")