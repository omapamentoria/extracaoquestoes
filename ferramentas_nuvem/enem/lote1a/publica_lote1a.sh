#!/bin/bash
# Refaz a gravacao do ENEM 2015-2019 (lote 1 A) no Banco-de-questoes. Uso: publica_lote1a.sh <banco> <pasta_int>
set -e
B=$1; T=$2; R=/home/user/extracaoquestoes; cd $R
(cd $B && git checkout -q -- final && git clean -fdq final imagens)
for p in P7581 P7583 P7577 P7579 P7585 P7587 P7589 P7591 P7593 P7595 P7597 P7599 P7605 P7607 P7609 P7611 P7613 P7615 P7617 P7619; do
  d=$(ls -d _banco/questoes/ENEM/*/$p); a=$(basename $(dirname $d))
  python3 ferramentas_nuvem/enem/integra.py $B/final/partes $d $T/int_$p.json ferramentas_nuvem/enem/correcoes/$a.json | head -1
done
C=$(ls ferramentas_nuvem/enem/correcoes/201[5-9].json | tr '\n' ',' | sed 's/,$//')
ID_BASE=160000 PARTE=34 REFAZER=comentarios_a_refazer_2026-11_enem2015a2019.json python3 ferramentas_nuvem/enem/publica.py $B $C $T/int_P7*.json | tail -1
python3 ferramentas_nuvem/enem/grava_classif.py $B/final/partes/banco_parte_34.json ferramentas_nuvem/enem/classif/2015a2019.txt 160000
python3 ferramentas_nuvem/enem/lote1a/area_antigas.py $B
