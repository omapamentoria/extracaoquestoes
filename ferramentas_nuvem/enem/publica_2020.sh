#!/bin/bash
# ENEM 2020: casa com o banco, grava (ramo do Banco-de-questoes ja criado a partir do padrao) e classifica.
# Uso: publica_2020.sh <Banco-de-questoes> <pasta de trabalho>
B=$1; S=$2; cd /home/user/extracaoquestoes; E=ferramentas_nuvem/enem
for p in P5400 P5402 P5404 P5406 P5410 P5418; do
  python3 $E/integra.py $B/final/partes _banco/questoes/ENEM/2020/$p $S/int_$p.json $E/correcoes/2020.json | grep -E "extraidas|gabarito diferente"
done
ID_BASE=150000 PARTE=33 REFAZER=comentarios_a_refazer_2026-11_enem2020.json python3 $E/publica.py $B $E/correcoes/2020.json $S/int_P5400.json $S/int_P5402.json $S/int_P5404.json $S/int_P5406.json $S/int_P5410.json $S/int_P5418.json | tail -3
python3 $E/grava_classif.py $B/final/partes/banco_parte_33.json $E/classif/2020.txt 0
for i in $(cut -d' ' -f1 $E/classif/2020_ajustes.txt); do
  f=$(grep -l "\"id\": $i," $B/final/partes/*.json | head -1); [ -z "$f" ] && f=$(python3 -c "import json,glob,sys;print([g for g in glob.glob('$B/final/partes/*.json') if any(q['id']==$i for q in json.load(open(g)))][0])")
  grep "^$i " $E/classif/2020_ajustes.txt > $S/aj_$i.txt; python3 $E/grava_classif.py $f $S/aj_$i.txt 0
  git -C $B show HEAD:${f#$B/} | head -c 2 | grep -q "\[{" || python3 -c "import json,sys;L=json.load(open(sys.argv[1]));json.dump(L,open(sys.argv[1],'w'),ensure_ascii=False,indent=0)" $f   # mantem o formato
done
