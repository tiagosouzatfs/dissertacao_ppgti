#!/usr/bin/env python3
"""
Benchmark runner for MQTT-SN
"""

import socket, struct, time, random, argparse, csv, os
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------
# Constantes MQTT-SN
# --------------------------
MQTTSN_CONNECT = 0x04
MQTTSN_CONNACK = 0x05
MQTTSN_REGISTER = 0x0A
MQTTSN_REGACK = 0x0B
MQTTSN_PUBLISH = 0x0C
MQTTSN_PUBACK = 0x0D
MQTTSN_PUBCOMP = 0x0E
MQTTSN_PUBREC = 0x0F
MQTTSN_PUBREL = 0x10
MQTTSN_DISCONNECT = 0x18

QOS_M1 = 0b11
QOS_0  = 0b00
QOS_1  = 0b01
QOS_2  = 0b10
TOPICIDTYPE_NORMAL = 0b00

RECV_TIMEOUT = 5.0
CONNECT_TIMEOUT = 5.0
REGISTER_TIMEOUT = 5.0
PUBLISH_TIMEOUT = 5.0
PUBREL_TIMEOUT = 5.0
DISCONNECT_TIMEOUT = 3.0

# --------------------------
# Builders MQTT-SN
# --------------------------
def build_connect(client_id, duration=60):
    flags = 0x02
    protocol_id = 0x01
    payload = struct.pack('>BBH', flags, protocol_id, duration) + client_id.encode('utf-8')
    return struct.pack('>BB', len(payload) + 2, MQTTSN_CONNECT) + payload

def build_register(topic_name, msg_id):
    topic_id = 0x0000
    payload = struct.pack('>HH', topic_id, msg_id) + topic_name.encode('utf-8')
    return struct.pack('>BB', len(payload) + 2, MQTTSN_REGISTER) + payload

def build_publish(qos_level, topic_id, msg_id, data):
    flags = ((qos_level & 0x03) << 5) | (TOPICIDTYPE_NORMAL & 0x03)
    msg_id_to_send = msg_id if qos_level != QOS_M1 else 0x0000
    header = struct.pack('>BHH', flags, topic_id, msg_id_to_send)
    payload = data if isinstance(data, (bytes, bytearray)) else data.encode('utf-8')
    length = len(header) + len(payload) + 2
    return struct.pack('>BB', length, MQTTSN_PUBLISH) + header + payload

def build_pubrel(msg_id):
    payload = struct.pack('>H', msg_id)
    return struct.pack('>BB', len(payload) + 2, MQTTSN_PUBREL) + payload

def build_disconnect():
    return struct.pack('>BB', 2, MQTTSN_DISCONNECT)

# --------------------------
# Envio / Recepção
# --------------------------
def send_packet(sock, packet_bytes, server_addr):
    sock.sendto(packet_bytes, server_addr)

def recv_mqttsn(sock, timeout=RECV_TIMEOUT):
    sock.settimeout(timeout)
    try:
        data, _ = sock.recvfrom(4096)
    except socket.timeout:
        return None
    if len(data) < 2:
        return None
    return data

# --------------------------
# Cliente individual
# --------------------------
def run_single_client(client_idx, gw_ip, gw_port, client_ip, qos_level, topic_name_param, mode_label, timeout_settings):
    result = {
        "cenario": "mqttsn",
        "qos": qos_level,
        "modo": mode_label,
        "cliente_id": client_idx,
        "t_fluxo_connect_ms": 0,
        "t_fluxo_register_ms": 0,
        "t_fluxo_publish_ms": 0,
        "t_fluxo_disconnect_ms": 0,
        "t_fluxo_total_ms": 0,
        "sucesso": 0
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((client_ip, 0))
    except Exception as e:
        print(f"[client {client_idx}] erro bind: {e}")
        sock.close()
        return result
    server_addr = (gw_ip, gw_port)

    if qos_level == QOS_M1:
        topic_name = "tt"
    elif qos_level == QOS_0:
        topic_name = "topic/teste/qos0"
    elif qos_level == QOS_1:
        topic_name = "topic/teste/qos1"
    else:
        topic_name = "topic/teste/qos2"

    client_id = f"bench_client_{client_idx}_{random.randint(1000,9999)}"
    msg_id = 0x0001
    data_msg = f"payload_for_client_{client_idx}"

    start_total = time.perf_counter()

    # QoS -1 → apenas Publish
    if qos_level == QOS_M1:
        t0 = time.perf_counter()
        send_packet(sock, build_publish(qos_level, 1, msg_id, data_msg), server_addr)
        t1 = time.perf_counter()
        result["t_fluxo_publish_ms"] = (t1 - t0) * 1000
        result["t_fluxo_total_ms"] = result["t_fluxo_publish_ms"]
        result["sucesso"] = 1
        sock.close()
        return result

    # CONNECT
    t0 = time.perf_counter()
    send_packet(sock, build_connect(client_id), server_addr)
    connack = recv_mqttsn(sock, timeout=timeout_settings.get("connect", CONNECT_TIMEOUT))
    t1 = time.perf_counter()
    if connack is None:
        sock.close()
        return result
    result["t_fluxo_connect_ms"] = (t1 - t0) * 1000

    # REGISTER / REGACK
    t0 = time.perf_counter()
    send_packet(sock, build_register(topic_name, msg_id), server_addr)
    regack = recv_mqttsn(sock, timeout=timeout_settings.get("register", REGISTER_TIMEOUT))
    t1 = time.perf_counter()
    if regack is None:
        sock.close()
        return result
    result["t_fluxo_register_ms"] = (t1 - t0) * 1000
    topic_id = struct.unpack('>H', regack[2:4])[0] if len(regack) >= 4 else 1

    # PUBLISH
    t0 = time.perf_counter()
    send_packet(sock, build_publish(qos_level, topic_id, msg_id, data_msg), server_addr)

    if qos_level == QOS_0:
        t1 = time.perf_counter()
        result["t_fluxo_publish_ms"] = (t1 - t0) * 1000

    elif qos_level == QOS_1:
        puback = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        t1 = time.perf_counter()
        result["t_fluxo_publish_ms"] = (t1 - t0) * 1000 if puback else 0

    elif qos_level == QOS_2:
        pubrec = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        if pubrec:
            send_packet(sock, build_pubrel(msg_id), server_addr)
            pubcomp = recv_mqttsn(sock, timeout=timeout_settings.get("pubrel", PUBREL_TIMEOUT))
        t1 = time.perf_counter()
        result["t_fluxo_publish_ms"] = (t1 - t0) * 1000 if pubrec else 0

    # DISCONNECT
    t0 = time.perf_counter()
    send_packet(sock, build_disconnect(), server_addr)
    t1 = time.perf_counter()
    result["t_fluxo_disconnect_ms"] = (t1 - t0) * 1000

    result["t_fluxo_total_ms"] = (
        result["t_fluxo_connect_ms"] +
        result["t_fluxo_register_ms"] +
        result["t_fluxo_publish_ms"] +
        result["t_fluxo_disconnect_ms"]
    )

    result["sucesso"] = 1 if result["t_fluxo_publish_ms"] > 0 else 0
    sock.close()
    return result

# --------------------------
# Execução em lote
# --------------------------
CSV_FIELDS = [
    "cenario","qos","modo","cliente_id",
    "t_fluxo_connect_ms","t_fluxo_register_ms","t_fluxo_publish_ms","t_fluxo_disconnect_ms",
    "t_fluxo_total_ms","sucesso"
]

def append_results_to_csv(filename, rows):
    first = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if first:
            writer.writeheader()
        writer.writerows(rows)

def run_benchmark_for_qos(gw_ip, gw_port, client_ip, qos_level, mode, repetitions=100, topic_name=None, timeout_settings=None):
    results = []
    mode_label = "paralelo" if mode == "parallel" else "serial"
    timeout_settings = timeout_settings or {}

    if mode == "parallel":
        with ThreadPoolExecutor(max_workers=min(200, repetitions)) as ex:
            futures = [ex.submit(run_single_client, i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings) for i in range(repetitions)]
            for fut in as_completed(futures):
                results.append(fut.result())
    else:
        for i in range(repetitions):
            results.append(run_single_client(i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings))
    return results

# --------------------------
# CLI principal
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gw", required=True)
    parser.add_argument("--port-gw", type=int, required=True)
    parser.add_argument("--client-ip", default="10.0.0.2")
    parser.add_argument("--mode", choices=["parallel","serial"], default="parallel")
    parser.add_argument("--reps", type=int, default=100)
    parser.add_argument("--qos", type=int, choices=[-1,0,1,2])
    parser.add_argument("--out", default="results/mqttsn.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    qos_list = [-1,0,1,2] if args.qos is None else [args.qos]

    for qos in qos_list:
        topic = { -1:"tt", 0:"topic/teste/qos0", 1:"topic/teste/qos1", 2:"topic/teste/qos2" }[qos]
        qlevel = { -1:QOS_M1, 0:QOS_0, 1:QOS_1, 2:QOS_2 }[qos]
        print(f"\n--- Executando QoS {qos} ---")
        res = run_benchmark_for_qos(args.gw, args.port_gw, args.client_ip, qlevel, args.mode, args.reps, topic)
        append_results_to_csv(args.out, res)
        valid = [r["t_fluxo_total_ms"] for r in res if r["t_fluxo_total_ms"]]
        print(f"Sucesso={sum(r['sucesso'] for r in res)}/{len(res)} | Média total={sum(valid)/len(valid):.2f} ms" if valid else "Sem dados válidos")

if __name__ == "__main__":
    main()
