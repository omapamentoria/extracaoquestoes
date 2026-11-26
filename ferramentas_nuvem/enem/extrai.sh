#!/bin/bash
# Extrai provas (2 de cada vez) e confere o gabarito com a leitura independente. Uso: extrai.sh PID...
cd /home/user/extracaoquestoes
L=/tmp/claude-0/-home-user-extracaoquestoes/d6cf449b-2258-57c8-874f-7af7d0e18afb/scratchpad
for p in "$@"; do
  timeout 1800 python3 _banco/codigo/06_extrair.py $p > $L/r_$p.log 2>&1 &
  while [ $(jobs -r | wc -l) -ge 2 ]; do sleep 2; done
done; wait
for p in "$@"; do
  echo "== $p"; grep -E "questões \(|PENDENTES|Traceback|Error" $L/r_$p.log
  d=$(ls -d _banco/questoes/ENEM/*/$p 2>/dev/null)
  g=$(python3 -c "import json;c={x['id']:x for x in json.load(open('_banco/catalogo_debug.json'))};print(c[c['$p']['gabarito_ids'].split()[0]]['caminho'])")
  [ -n "$d" ] && python3 ferramentas_nuvem/enem/gab_enem.py "$g" $d/questoes.json | tail -4
done
echo FIM
