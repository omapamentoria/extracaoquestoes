#!/bin/bash
# Depois das fases 3-5: tira da lista de OCR as provas de ENEM/SSA que falharam por erro de codigo ja corrigido
# (poucas questoes / nenhuma questao) e extrai de novo. Provas de texto ruim ou com maioria PENDENTE continuam na lista.
cd "$(dirname "$0")/.."
while pgrep -f "fases_3a5.sh" >/dev/null; do sleep 60; done
python3 - <<'PY'
import re
p = "docs/lotes/para_ocr.md"; L = open(p, encoding="utf-8").read().split("\n")
fora = lambda l: l.startswith("* ") and re.search(r"— (ENEM|SSA) ", l) and re.search(r"só \d+ questões|nenhuma questão", l)
open(p, "w", encoding="utf-8").write("\n".join(l for l in L if not fora(l)))
PY
python3 ferramentas_nuvem/fase.py enem-r ENEM 10
python3 ferramentas_nuvem/fase.py ssa-r SSA 10
echo "REFACAO CONCLUIDA"
