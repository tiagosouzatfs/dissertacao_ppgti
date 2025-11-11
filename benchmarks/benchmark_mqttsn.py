#!/usr/bin/env python3
"""
Benchmark runner for MQTT-SN

- Mede tempos de execução detalhados por cliente (1..100) para QoS -1,0,1,2
- Suporta modos paralelo (100 publishers simultâneos) e serial (1 por vez)
- Gera CSV: results/mqttsn.csv

Uso:
  python3 benchmark_mqttsn.py --gw 10.0.0.1 --port 1884 --mode parallel
  python3 benchmark_mqttsn.py --gw 10.0.0.1 --port 1884 --mode serial --qos 1
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
        "cenario": "mqttsn_puro",
        "qos": qos_level,
        "modo": mode_label,
        "cliente_id": client_idx,
        "t_connect_ms": None,
        "t_register_ms": None,
        "t_publish_ms": None,
        "t_puback_ms": None,
        "t_pubrec_ms": None,
        "t_relcomp_ms": None,
        "t_disconnect_ms": None,
        "t_total_ms": None,
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

    # tópicos por QoS
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
    data_msg = ("payload_for_client_%d" % client_idx)

    start_total = time.perf_counter()

    # QoS -1 → só publish
    if qos_level == QOS_M1:
        pub_start = time.perf_counter()
        mqtt_publish = build_publish(qos_level, 1, msg_id, data_msg)
        send_packet(sock, mqtt_publish, server_addr)
        time.sleep(0.01)
        pub_end = time.perf_counter()
        result["t_publish_ms"] = (pub_end - pub_start) * 1000
        result["t_total_ms"] = (pub_end - start_total) * 1000
        result["sucesso"] = 1
        sock.close()
        return result

    # CONNECT
    conn_start = time.perf_counter()
    pkt_connect = build_connect(client_id)
    send_packet(sock, pkt_connect, server_addr)
    connack_payload = recv_mqttsn(sock, timeout=timeout_settings.get("connect", CONNECT_TIMEOUT))
    conn_end = time.perf_counter()
    if connack_payload is None:
        print(f"[client {client_idx}] CONNACK timeout")
        sock.close()
        result["t_total_ms"] = (time.perf_counter() - start_total) * 1000
        return result
    result["t_connect_ms"] = (conn_end - conn_start) * 1000

    # REGISTER → REGACK
    reg_start = time.perf_counter()
    pkt_register = build_register(topic_name, msg_id)
    send_packet(sock, pkt_register, server_addr)
    regack_payload = recv_mqttsn(sock, timeout=timeout_settings.get("register", REGISTER_TIMEOUT))
    reg_end = time.perf_counter()
    if regack_payload is None:
        print(f"[client {client_idx}] REGACK timeout")
        sock.close()
        result["t_total_ms"] = (time.perf_counter() - start_total) * 1000
        return result
    try:
        topic_id = struct.unpack('>H', regack_payload[2:4])[0]
    except Exception:
        topic_id = 0x0001
    result["t_register_ms"] = (reg_end - reg_start) * 1000

    # PUBLISH
    pub_start = time.perf_counter()
    mqtt_publish = build_publish(qos_level, topic_id, msg_id, data_msg)
    send_packet(sock, mqtt_publish, server_addr)

    if qos_level == QOS_0:
        pub_end = time.perf_counter()
        result["t_publish_ms"] = (pub_end - pub_start) * 1000
        pkt_disconnect = build_disconnect()
        send_packet(sock, pkt_disconnect, server_addr)
        result["t_total_ms"] = (time.perf_counter() - start_total) * 1000
        result["sucesso"] = 1
        sock.close()
        return result

    if qos_level == QOS_1:
        puback_payload = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        puback_time = time.perf_counter()
        if puback_payload is None:
            print(f"[client {client_idx}] PUBACK timeout")
        else:
            result["t_puback_ms"] = (puback_time - pub_start) * 1000
        result["t_publish_ms"] = (puback_time - pub_start) * 1000 if result["t_puback_ms"] else None
        pkt_disconnect = build_disconnect()
        send_packet(sock, pkt_disconnect, server_addr)
        result["t_total_ms"] = (time.perf_counter() - start_total) * 1000
        result["sucesso"] = 1 if result["t_puback_ms"] else 0
        sock.close()
        return result

    if qos_level == QOS_2:
        pubrec_payload = recv_mqttsn(sock, timeout=timeout_settings.get("publish", PUBLISH_TIMEOUT))
        pubrec_time = time.perf_counter()
        if pubrec_payload is None:
            print(f"[client {client_idx}] PUBREC timeout")
            sock.close()
            return result
        result["t_pubrec_ms"] = (pubrec_time - pub_start) * 1000
        pkt_pubrel = build_pubrel(msg_id)
        send_packet(sock, pkt_pubrel, server_addr)
        pubcomp_payload = recv_mqttsn(sock, timeout=timeout_settings.get("pubrel", PUBREL_TIMEOUT))
        rel_end = time.perf_counter()
        if pubcomp_payload is None:
            print(f"[client {client_idx}] PUBCOMP timeout")
        else:
            result["t_relcomp_ms"] = (rel_end - pubrec_time) * 1000
        result["t_publish_ms"] = (rel_end - pub_start) * 1000
        pkt_disconnect = build_disconnect()
        send_packet(sock, pkt_disconnect, server_addr)
        result["t_total_ms"] = (time.perf_counter() - start_total) * 1000
        result["sucesso"] = 1 if result["t_relcomp_ms"] else 0
        sock.close()
        return result

    sock.close()
    return result

# --------------------------
# Execução em lote
# --------------------------
CSV_FIELDS = [
    "cenario","qos","modo","cliente_id",
    "t_connect_ms","t_register_ms","t_publish_ms","t_puback_ms","t_pubrec_ms","t_relcomp_ms","t_disconnect_ms",
    "t_total_ms","sucesso"
]

def append_results_to_csv(filename, rows):
    first = not os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if first:
            writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in CSV_FIELDS})

def run_benchmark_for_qos(gw_ip, gw_port, client_ip, qos_level, mode, repetitions=100, topic_name=None, timeout_settings=None):
    results = []
    mode_label = "paralelo" if mode == "parallel" else "serial"
    if timeout_settings is None:
        timeout_settings = {}

    if mode == "parallel":
        with ThreadPoolExecutor(max_workers=min(200, repetitions)) as ex:
            futures = {ex.submit(run_single_client, i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings): i+1 for i in range(repetitions)}
            for fut in as_completed(futures):
                try:
                    r = fut.result()
                    results.append(r)
                except Exception as e:
                    print("Exception:", e)
    else:
        for i in range(repetitions):
            r = run_single_client(i+1, gw_ip, gw_port, client_ip, qos_level, topic_name, mode_label, timeout_settings)
            results.append(r)
    return results

# --------------------------
# CLI principal
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gw", required=True, help="IP do gateway MQTT-SN")
    parser.add_argument("--port", type=int, required=True, help="Porta UDP do gateway")
    parser.add_argument("--client-ip", default="10.0.0.2", help="IP local do cliente")
    parser.add_argument("--mode", choices=["parallel","serial"], default="parallel", help="Modo de execução")
    parser.add_argument("--reps", type=int, default=100, help="Número de clientes publishers (padrão 100)")
    parser.add_argument("--qos", type=int, choices=[-1,0,1,2], help="Executar somente este QoS")
    parser.add_argument("--out", default="results/mqttsn.csv", help="Arquivo CSV de saída")
    args = parser.parse_args()

    gw_ip, gw_port, client_ip = args.gw, args.port, args.client_ip
    mode, repetitions, outfile = args.mode, args.reps, args.out

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    qos_list = [-1,0,1,2] if args.qos is None else [args.qos]

    print("=== Benchmark MQTT-SN ===")
    print(f"GW: {gw_ip}:{gw_port} | Cliente: {client_ip} | Modo: {mode} | Repetições: {repetitions}")
    print("QoS:", qos_list)

    for qos in qos_list:
        topic_name = {
            -1: "tt",
            0: "topic/teste/qos0",
            1: "topic/teste/qos1",
            2: "topic/teste/qos2"
        }[qos]
        print(f"\n--- Executando QoS {qos} ({mode}) topic={topic_name} ---")
        qlevel = QOS_M1 if qos==-1 else (QOS_0 if qos==0 else (QOS_1 if qos==1 else QOS_2))
        res = run_benchmark_for_qos(gw_ip, gw_port, client_ip, qlevel, mode, repetitions=repetitions, topic_name=topic_name)
        append_results_to_csv(outfile, res)
        times = [r["t_total_ms"] for r in res if r["t_total_ms"]]
        succ = sum(1 for r in res if r["sucesso"])
        print(f"Sucesso={succ}/{len(res)} | média tempo total={sum(times)/len(times):.2f} ms" if times else "Sem tempos válidos")

    print("\nFinalizado. Resultados em", outfile)

if __name__ == "__main__":
    main()
