import subprocess
import csv
import time

# --- CONFIGURAÇÃO ---
CONTAINER_NAME = "mn.gw_bk"   # Nome do container do Gateway/Broker
DURATION_SEC = 180            # Tempo total da coleta após o início
INTERVAL = 0.1                # Coleta a cada 100ms
OUTPUT_FILE = "metrics_docker_stats.csv"

def collect_metrics():
    print(f"--- Iniciando monitoramento do container: {CONTAINER_NAME} ---")
    print(f"--- Frequência: {INTERVAL}s | Duração: {DURATION_SEC}s ---")
    
    # Prepara o arquivo CSV
    with open(OUTPUT_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['relative_time', 'cpu_percent', 'mem_percent'])

        start_time = time.time()
        
        try:
            while (time.time() - start_time) < DURATION_SEC:
                loop_start = time.time()
                
                # Executa o docker stats formatado (sem símbolos de % ou unidades)
                cmd = [
                    "docker", "stats", CONTAINER_NAME, 
                    "--no-stream", 
                    "--format", "{{.CPUPerc}},{{.MemPerc}}"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Limpa os símbolos de '%' da string retornada
                    raw_data = result.stdout.replace('%', '').strip()
                    if ',' in raw_data:
                        # Divide CPU e Memória
                        parts = raw_data.split(',')
                        if len(parts) == 2:
                            cpu = parts[0].replace('%', '')
                            mem = parts[1].replace('%', '')
                            
                            relative_tick = round(time.time() - start_time, 2)
                            writer.writerow([relative_tick, cpu, mem])
                
                # Controle de precisão do intervalo
                elapsed = time.time() - loop_start
                wait_time = max(0, INTERVAL - elapsed)
                time.sleep(wait_time)
                
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário.")
            
    print(f"\n[SUCESSO] Coleta finalizada. Dados salvos em: {OUTPUT_FILE}")

if __name__ == "__main__":
    print(f"Aguardando o container '{CONTAINER_NAME}' iniciar...")
    
    # Loop de espera ativa (Polling) até o container aparecer
    while True:
        try:
            check_docker = subprocess.run(
                ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--filter", "status=running", "-q"], 
                capture_output=True, 
                text=True
            )
            
            # Se o comando retornar um ID, o container está rodando
            if check_docker.stdout.strip():
                print(f"Container '{CONTAINER_NAME}' detectado! Iniciando medição agora.")
                collect_metrics()
                break
            
            time.sleep(1) # Verifica a cada 1 segundo para não sobrecarregar a CPU
            
        except KeyboardInterrupt:
            print("\nMonitoramento cancelado antes do início.")
            break