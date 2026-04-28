import subprocess
import csv
import time
import sys

try:
    MODE = sys.argv[1]
    N_MSGS = sys.argv[2]
except IndexError:
    print("Erro: Você deve especificar o modo e quantidade de mensagens. Exemplo: python3 monitoring.py mqttsn 1k")
    sys.exit(1)

CONTAINERS = ["mn.s1", "mn.gw", "mn.bk"]
DURATION_SEC = 720
INTERVAL = 1
OUTPUT_FILE = f"metrics_docker_stats_{MODE}_{N_MSGS}.csv"

def get_net_stats(container):
    """Coleta bytes e pacotes via docker exec."""
    try:
        cmd = ["docker", "exec", container, "cat", "/proc/net/dev"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "eth0" in line:
                data = line.split()
                # RX_Bytes (1), RX_Packets (2), TX_Bytes (9), TX_Packets (10)
                return [data[1], data[2], data[9], data[10]]
    except:
        pass
    return ["0", "0", "0", "0"]

def collect_metrics():
    print(f"--- Iniciando monitoramento dos containers: {CONTAINERS} ---")
    print(f"--- Modo: {MODE} | Arquivo: {OUTPUT_FILE} ---")
    
    with open(OUTPUT_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Cabeçalho atualizado com colunas de rede para cada container
        header = ['relative_time']
        for c in ['s1', 'gw', 'bk']:
            header += [f'{c}_cpu', f'{c}_mem', f'{c}_rx_bytes', f'{c}_rx_pkts', f'{c}_tx_bytes', f'{c}_tx_pkts']
        writer.writerow(header)

        start_time = time.time()
        
        try:
            while (time.time() - start_time) < DURATION_SEC:
                loop_start = time.time()
                
                cmd = [
                    "docker", "stats", *CONTAINERS, 
                    "--no-stream", 
                    "--format", "{{.CPUPerc}},{{.MemPerc}}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) == len(CONTAINERS):
                        row = [round(time.time() - start_time, 2)]
                        
                        # Itera sobre os resultados do stats e busca a rede individualmente
                        for i, line in enumerate(lines):
                            parts = line.replace('%', '').split(',')
                            cpu_mem = [parts[0].strip(), parts[1].strip()]
                            net_data = get_net_stats(CONTAINERS[i])
                            
                            row.extend(cpu_mem + net_data)
                        
                        writer.writerow(row)
                        f.flush() # Garante a escrita imediata
                
                elapsed = time.time() - loop_start
                wait_time = max(0, INTERVAL - elapsed)
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário.")
            
    print(f"\n[SUCESSO] Coleta finalizada. Dados salvos em: {OUTPUT_FILE}")

if __name__ == "__main__":
    print(f"Verificando se os containers {CONTAINERS} estão ativos...")
    while True:
        try:
            check = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
            if all(name in check.stdout for name in CONTAINERS):
                print(f"Containers detectados! Iniciando medição.")
                collect_metrics()
                break
            time.sleep(1)
        except KeyboardInterrupt:
            break