#!/bin/bash

CONTAINER_NAME="mn.gw_bk"
OUTPUT_FILE="results/emqx_metrics.csv"
DURATION=30     # segundos
INTERVAL=0.5    # 1 décimo de segundo

# Header
echo "timestamp,container,cpu_percent,mem_percent" > $OUTPUT_FILE

start_time=$(date +%s)

while true
do
  current_time=$(date +%s)
  elapsed=$((current_time - start_time))

  # Para após 30 segundos
  if [ $elapsed -ge $DURATION ]; then
    break
  fi

  docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemPerc}}" $CONTAINER_NAME | while IFS=',' read -r name cpu memperc
  do
    timestamp=$(date +"%Y-%m-%d %H:%M:%S.%3N")
    echo "$timestamp,$name,$cpu,$memperc" >> $OUTPUT_FILE
  done

  sleep $INTERVAL
done

echo "Coleta finalizada! Dados salvos em $OUTPUT_FILE"