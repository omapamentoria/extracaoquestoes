#!/bin/bash
# Fases 3, 4 e 5 em sequencia, cada uma no seu repositorio. Espera as fases 1-2 terminarem. Retomavel: fase.py pula o
# que ja foi extraido, entao rodar de novo continua de onde parou. Log em /tmp/fases_3a5.log
cd "$(dirname "$0")/.."
while pgrep -f "todas_fases.sh" >/dev/null; do sleep 30; done
python3 ferramentas_nuvem/fase.py sim- SIMULADO_ENEM,SIMULADO_SSA 10 /home/user/banco-simulados
python3 ferramentas_nuvem/fase.py vest- FUVEST,UNICAMP,UERJ,UNESP,SIMULADO_FUVEST,SIMULADO_UERJ,SIMULADO_UNESP,SIMULADO_UNICAMP 10 /home/user/banco-vestibulares
python3 ferramentas_nuvem/fase.py dem- DEMAIS 10 /home/user/banco-demais
echo "FASES 3-5 CONCLUIDAS"
