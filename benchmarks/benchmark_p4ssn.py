#!/usr/bin/env python3
import socket
import struct
import random
import time
import os
import csv

# Constantes de Protocolo
MQTTSN_CONNECT, MQTTSN_CONNACK = 0x04, 0x05
MQTTSN_REGISTER, MQTTSN_REGACK = 0x0A, 0x0B
MQTTSN_PUBLISH, MQTTSN_PUBACK = 0x0C, 0x0D
MQTTSN_PUBREC, MQTTSN_PUBREL = 0x0F, 0x10
MQTTSN_PUBCOMP, MQTTSN_DISCONNECT = 0x0E, 0x18

# Segurança P4SSN
SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

QOS_M1, QOS_0, QOS_1, QOS_2 = 0b11, 0b00, 0b01, 0b10
GW_IP, GW_PORT = "10.0.0.1", 1884

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
    output = [b ^ (mask_bytes[i%64] ^ (otp & 0xFF if i%2==0 else (otp>>8)&0xFF)) for i, b in enumerate(data_bytes)]
    return struct.pack('>H', payload_salt) + bytes(output)

class P4SSNBenchmark:
    def __init__(self, client_ip):
        self.client_ip = client_ip

    def run_test(self, qos, retain, iteration):
        client_id_rand = f"p4_{iteration}_{random.randint(1000, 9999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(2.5)
        
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        current_topic_id = 1 
        topic_type = 0x01    
        data_str = "P4SSN_TEST_DATA"
        
        try:
            # 1. Fluxo de Preparação
            if qos != QOS_M1:
                clean = 0x00 if qos == QOS_2 else 0x04
                conn = struct.pack('>BBH', clean, 0x01, 60) + client_id_rand.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                sock.recvfrom(1024)

                if not (qos == QOS_0 and retain == 0):
                    topic_name = b"p4benchmark"
                    reg_body = struct.pack('>HH', 0x0000, msg_id) + topic_name
                    sock.sendto(struct.pack('>BB', len(reg_body)+2, MQTTSN_REGISTER) + reg_body, (GW_IP, GW_PORT))
                    regack, _ = sock.recvfrom(1024)
                    current_topic_id = struct.unpack('>H', regack[4:6])[0]
                    topic_type = 0x00 

            # --- TIMING ---
            t_start_pub = time.perf_counter()
            
            salt = msg_id
            flags = ((qos & 0x03) << 5) | ((retain & 0x01) << 4) | (topic_type & 0x03)
            topic_enc = otp_encrypt_topic(current_topic_id, salt)
            payload_enc = otp_process_data(data_str, salt)
            
            header = struct.pack('>BB BHH', len(payload_enc)+7, MQTTSN_PUBLISH, flags, topic_enc, salt)
            sock.sendto(header + payload_enc, (GW_IP, GW_PORT))
            t_end_pub = time.perf_counter()

            if qos == QOS_1:
                sock.recvfrom(1024)
            elif qos == QOS_2:
                rec, _ = sock.recvfrom(1024)
                if rec[1] == MQTTSN_PUBREC:
                    sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), (GW_IP, GW_PORT))
                    sock.recvfrom(1024)
            
            t_end_total = time.perf_counter()

            if qos != QOS_M1:
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))

            sock.close()
            
            # Print formatado igual ao MQTT-SN
            q_label = -1 if qos == 0b11 else qos
            print(f"[{iteration}/100] QoS: {q_label} | Retain: {retain} | Total: {round((t_end_total - t_start_pub)*1000, 2)}ms")

            qos_csv = f"{q_label} sem retain" if q_label == 0 and retain == 0 else (f"0 com retain" if q_label == 0 else str(q_label))
            return {
                "cenario": "p4ssn", "qos": qos_csv, "cliente_id": client_id_rand,
                "t_fluxo_publish_ms": round((t_end_pub - t_start_pub)*1000, 4),
                "t_fluxo_total_ms": round((t_end_total - t_start_pub)*1000, 4)
            }

        except Exception:
            sock.close()
            return None

if __name__ == "__main__":
    client = P4SSNBenchmark("10.0.0.2")
    if not os.path.exists('results'): os.makedirs('results')
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)]
    
    with open('results/p4ssn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "cliente_id", "t_fluxo_publish_ms", "t_fluxo_total_ms"])
        writer.writeheader()
        for qos, ret in test_cases:
            for i in range(1, 101):
                res = client.run_test(qos, ret, i)
                if res: writer.writerow(res)
                
    print(f"\nCSV results/p4ssn.csv gerado.")