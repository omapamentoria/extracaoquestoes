#!/bin/bash
# uso: roda.sh PID... (2 de cada vez)
cd ~/mnt/BM/_banco
for p in "$@"; do
  python3 codigo/06_extrair.py $p > /tmp/r_$p.log 2>&1 &
  while [ $(jobs -r | wc -l) -ge 2 ]; do sleep 1; done
done
wait
for p in "$@"; do echo "== $p"; grep -E "formato|páginas de reda|questões \(|números faltando|Traceback|Error|PENDENTES" /tmp/r_$p.log; done
