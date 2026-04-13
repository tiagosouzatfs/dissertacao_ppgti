#!/usr/bin/env python3
import socket
import struct
import random
import time
import os
import csv

# =============================================================================
# Constantes e Segurança P4SSN
# =============================================================================
MQTTSN_CONNECT, MQTTSN_CONNACK = 0x04, 0x05
MQTTSN_PUBLISH, MQTTSN_PUBACK = 0x0C, 0x0D
MQTTSN_PUBREC, MQTTSN_PUBREL = 0x0F, 0x10
MQTTSN_PUBCOMP, MQTTSN_DISCONNECT = 0x0E, 0x18

SECRET_TOPIC_ID = 0xB7A3
SECRET_DATA_PUBLISH = 0x8D93D01BEE9B416847B69D483BDFB0D6D4D329D98B278AD866E6B17076638B6F7BA810790B07C638825AE5F9B05FABCF7EC35360992DB924F0ECFEEDA972170B

QOS_M1, QOS_0, QOS_1, QOS_2 = 0b11, 0b00, 0b01, 0b10
TOPICIDTYPE_PREDEFINED = 0b01
PREDEFINED_TOPIC_ID = 10

GW_IP, GW_PORT = "10.0.0.2", 1884
CLIENT_IP = "10.0.0.3"
TIMEOUT = 5.0

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

    def run_iteration(self, qos, retain, iteration):
        client_id = f"p4_{iteration}_{random.randint(100, 999)}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.client_ip, 0))
        sock.settimeout(TIMEOUT)
        
        msg_id = (iteration + (qos * 100)) % 0xFFFF
        data_str = "P4SSN_SECURE_DATA_BENCHMARK"
        
        t_start_flow = time.perf_counter()
        t_end_total = 0
        
        try:
            if qos != QOS_M1:
                # CONNECT
                conn = struct.pack('>BBH', 0x04, 0x01, 60) + client_id.encode()
                sock.sendto(struct.pack('>BB', len(conn)+2, MQTTSN_CONNECT) + conn, (GW_IP, GW_PORT))
                sock.recvfrom(1024)

            # PUBLISH (Sempre Predefinido)
            salt = msg_id if qos != QOS_M1 else random.randint(1, 0xFFFF)
            flags = ((qos & 0x03) << 5) | ((retain & 0x01) << 4) | TOPICIDTYPE_PREDEFINED
            
            topic_enc = otp_encrypt_topic(PREDEFINED_TOPIC_ID, salt)
            payload_enc = otp_process_data(data_str, salt)
            
            header = struct.pack('>BB BHH', len(payload_enc)+7, MQTTSN_PUBLISH, flags, topic_enc, salt)
            sock.sendto(header + payload_enc, (GW_IP, GW_PORT))
            
            if qos == QOS_1:
                sock.recvfrom(1024)
            elif qos == QOS_2:
                rec, _ = sock.recvfrom(1024)
                if rec[1] == MQTTSN_PUBREC:
                    sock.sendto(struct.pack('>BBH', 4, MQTTSN_PUBREL, msg_id), (GW_IP, GW_PORT))
                    sock.recvfrom(1024)
            
            if qos != QOS_M1:
                # DISCONNECT
                sock.sendto(struct.pack('>BB', 2, MQTTSN_DISCONNECT), (GW_IP, GW_PORT))

            t_end_total = time.perf_counter()
        except (socket.timeout, Exception):
            t_start_flow = t_end_total = 0
        finally:
            sock.close()

        total_ms = (t_end_total - t_start_flow) * 1000 if t_end_total > 0 else 0
        q_label = -1 if qos == 0b11 else qos
        status = "OK" if total_ms > 0 or qos == QOS_M1 else "FAIL"
        print(f"[{iteration:03}/100] P4SSN | QoS: {q_label} | {status} | {round(total_ms, 2)}ms")

        return {"cenario": "p4ssn", "qos": qos, "retain": retain, "t_flow_ms": round(total_ms, 4)}

if __name__ == "__main__":
    bench = P4SSNBenchmark(CLIENT_IP)
    test_cases = [(QOS_M1, 0), (QOS_0, 0), (QOS_0, 1), (QOS_1, 0), (QOS_2, 0)]
    with open('/root/p4ssn.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["cenario", "qos", "retain", "t_flow_ms"])
        writer.writeheader()
        for qos, ret in test_cases:
            print(f"\n>>> Bateria P4SSN: QoS {qos} | Retain {ret}")
            time.sleep(2)
            for i in range(1, 101):
                writer.writerow(bench.run_iteration(qos, ret, i))
                time.sleep(0.05)