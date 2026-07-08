#!/usr/bin/env bash
# Extrai metrics.jsonl de todos os containers node* e mescla num único arquivo.
# Uso: ./collect_metrics.sh [diretório_de_saída]
#
# Exemplos:
#   ./collect_metrics.sh                      → salva em ./metrics_output/<timestamp>/
#   ./collect_metrics.sh /tmp/experimento_1   → salva no caminho especificado

set -euo pipefail

METRICS_PATH_IN_CONTAINER="/app/metrics.jsonl"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="${1:-./metrics_output/${TIMESTAMP}}"
MERGED_FILE="${OUTPUT_DIR}/metrics_all.jsonl"

mkdir -p "$OUTPUT_DIR"

echo "=== Extração de métricas BBYOR ==="
echo "Destino: ${OUTPUT_DIR}"
echo ""

# Descobre containers cujo nome contém "node" e estão rodando
CONTAINERS=$(podman ps --filter "name=node" --format "{{.Names}}" | sort -V)

if [ -z "$CONTAINERS" ]; then
    echo "Nenhum container com 'node' no nome encontrado em execução."
    exit 1
fi

TOTAL=0
COLETADOS=0
> "$MERGED_FILE"   # limpa/cria o arquivo mesclado

while IFS= read -r CONTAINER; do
    TOTAL=$((TOTAL + 1))
    DEST="${OUTPUT_DIR}/metrics_${CONTAINER}.jsonl"

    # Verifica se o arquivo existe no container antes de copiar
    if podman exec "$CONTAINER" test -f "$METRICS_PATH_IN_CONTAINER" 2>/dev/null; then
        podman cp "${CONTAINER}:${METRICS_PATH_IN_CONTAINER}" "$DEST" 2>/dev/null
        LINES=$(wc -l < "$DEST")
        echo "  [OK] ${CONTAINER}: ${LINES} entradas → ${DEST}"
        cat "$DEST" >> "$MERGED_FILE"
        COLETADOS=$((COLETADOS + 1))
    else
        echo "  [--] ${CONTAINER}: metrics.jsonl não encontrado (container pode não ter processado desafios ainda)"
    fi
done <<< "$CONTAINERS"

echo ""
echo "=== Resumo ================================================"
echo "  Containers encontrados : ${TOTAL}"
echo "  Com métricas coletadas : ${COLETADOS}"

if [ -s "$MERGED_FILE" ]; then
    TOTAL_ENTRIES=$(wc -l < "$MERGED_FILE")
    echo "  Total de entradas      : ${TOTAL_ENTRIES}"
    echo "  Arquivo mesclado       : ${MERGED_FILE}"
    echo ""
    echo "  Operações registradas:"
    # Conta entradas por operação sem depender de jq
    grep -o '"operation": *"[^"]*"' "$MERGED_FILE" \
        | sed 's/"operation": *"//;s/"//' \
        | sort | uniq -c | sort -rn \
        | awk '{printf "    %-40s %s entradas\n", $2, $1}'
else
    echo "  Nenhuma métrica coletada."
fi

echo "==========================================================="
