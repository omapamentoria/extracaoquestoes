#!/bin/bash
# Provas discursivas (questao + gabarito discursivo) e, depois, nova repescagem com o codigo atual.
# Espera o que estiver rodando. Logs /tmp/disc.log e /tmp/repesca2.log
cd "$(dirname "$0")/.."
while pgrep -f "refaz_lista.py" >/dev/null; do sleep 60; done
python3 ferramentas_nuvem/refaz_lista.py disc > /tmp/disc.log 2>&1
echo "DISCURSIVAS CONCLUIDAS" >> /tmp/disc.log
python3 ferramentas_nuvem/refaz_lista.py > /tmp/repesca2.log 2>&1
