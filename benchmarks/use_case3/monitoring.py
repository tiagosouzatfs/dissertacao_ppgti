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
DURATION_SEC = 120
INTERVAL = 1
OUTPUT_FILE = f"metrics_docker_stats_{MODE}_{N_MSGS}.csv"

def collect_metrics():
    print(f"--- Iniciando monitoramento dos containers: {CONTAINERS} ---")
    print(f"--- Modo: {MODE} | Arquivo: {OUTPUT_FILE} ---")
    
    with open(OUTPUT_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        # Cabeçalho para os dois containers
        writer.writerow(['relative_time', 's1_cpu', 's1_mem', 'gw_cpu', 'gw_mem', 'bk_cpu', 'bk_mem'])

        start_time = time.time()
        
        try:
            while (time.time() - start_time) < DURATION_SEC:
                loop_start = time.time()
                
                # Coleta stats de todos os containers de uma vez
                cmd = [
                    "docker", "stats", *CONTAINERS, 
                    "--no-stream", 
                    "--format", "{{.CPUPerc}},{{.MemPerc}}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) == len(CONTAINERS):
                        # Tempo relativo formatado para 2 casas decimais conforme seu script
                        row = [round(time.time() - start_time, 2)]
                        for line in lines:
                            parts = line.replace('%', '').split(',')
                            row.extend([parts[0].strip(), parts[1].strip()])
                        
                        writer.writerow(row)
                
                # Sincronização para manter o intervalo de 1s
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