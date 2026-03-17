#!/bin/bash

# 1. Localiza o PID do beam.smp
#PID=$(ps -ef | grep 'beam.smp' | grep -v grep | awk '{print $2}' | head -n 1)
PID=1

if [ -z "$PID" ]; then
    echo "Erro: Processo EMQX não encontrado."
    exit 1
fi

# 2. Configurações
DURATION=30
INTERVAL=0.1
OUTPUT="results/emqx.csv"

mkdir -p results
echo "timestamp,cpu_percent,memory_percent" > $OUTPUT

echo "Monitorando PID $PID por $DURATION segundos ..."

# Tempo inicial em milissegundos
START_MS=$(date +%s%3N)

# Loop de captura (300 iterações para 30s com 0.1s de intervalo)
for ((i=0; i<(DURATION*10); i++)); do
    NOW_MS=$(date +%s%3N)
    
    # Cálculo de tempo decorrido em ms (aritmética de shell)
    ELAPSED_MS=$((NOW_MS - START_MS))
    
    # Formata o timestamp (ex: 1200ms -> 1.20)
    SEC=$((ELAPSED_MS / 1000))
    MS=$(( (ELAPSED_MS % 1000) / 10 )) # Pega duas casas decimais
    # Garante que MS tenha dois dígitos (ex: .05 em vez de .5)
    TIMESTAMP=$(printf "%d.%02d" $SEC $MS)

    # Coleta via top
    STATS=$(top -b -n 1 -p $PID | tail -n 1 | awk '{print $9 "," $10}')
    
    if [ -z "$STATS" ]; then 
        echo "Monitoramento interrompido: PID finalizado."
        break 
    fi

    echo "$TIMESTAMP,$STATS" >> $OUTPUT

    # Sleep aceita decimais na maioria dos sistemas
    sleep $INTERVAL
done

echo "Concluído! Resultados em $OUTPUT"