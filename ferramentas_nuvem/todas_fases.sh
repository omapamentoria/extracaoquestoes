#!/bin/bash
# Roda as fases do banco em sequencia (cada lote vai para o GitHub ao terminar). Log em /tmp/fases.log
cd "$(dirname "$0")/.."
python3 ferramentas_nuvem/fase.py enem- ENEM 10
python3 ferramentas_nuvem/fase.py ssa- SSA 10
echo "FASES 1-2 CONCLUIDAS"
