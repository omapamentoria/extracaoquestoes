#!/bin/bash
# uso: [PAR=4] roda2.sh PID... -> extrai PAR provas de cada vez; cada prova tem no maximo 30 min (prova travada nao
# para a fila) e o tesseract usa 1 nucleo (com 4 provas em paralelo, varios nucleos por chamada so disputam a CPU)
cd ~/mnt/BM/_banco
export OMP_THREAD_LIMIT=1
for p in "$@"; do
  timeout 1800 python3 codigo/06_extrair.py $p > /tmp/r_$p.log 2>&1 &
  while [ $(jobs -r | wc -l) -ge ${PAR:-2} ]; do sleep 1; done
done
wait
for p in "$@"; do echo "== $p"; grep -E "formato|questões \(|Traceback|Error|PENDENTES" /tmp/r_$p.log; done
