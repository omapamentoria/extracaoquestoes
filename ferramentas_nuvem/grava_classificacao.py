# Grava a classificacao (area > materia > assunto > subassunto) nas partes do banco (final/partes), nos campos que a
# question-bank-sync usa direto: area_codigo, materia_codigo, assunto_codigo, subassunto_codigo.
#  - questao ja classificada na plataforma: os codigos que ela ja tem (mapa da plataforma);
#  - as outras: unificacao/classificacao.json (Fase 5b + revisao).
# Questao sem classificacao fica listada (nao inventa).
# Uso: python3 ferramentas_nuvem/grava_classificacao.py <Banco-de-questoes (ramo claude/banco-unificado)>
import json, os, sys, glob, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = sys.argv[1]
M = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
SUB = {s["codigo"]: s for s in M["subassuntos"]}; ASS = {a["codigo"]: a for a in M["assuntos"]}; MAT = {m["codigo"]: m for m in M["materias"]}
ja = {q["id"]: q["subassunto"] for q in M["questoes"] if q.get("subassunto")}
cls = json.load(open(os.path.join(R, "unificacao", "classificacao.json"), encoding="utf-8"))
cont, sem = collections.Counter(), []
for f in sorted(glob.glob(os.path.join(DEST, "final", "partes", "banco_parte_*.json"))):
    lista = json.load(open(f, encoding="utf-8"))
    for q in lista:
        sub = ja.get(q["id"]) or (cls.get(str(q["id"])) or {}).get("subassunto_codigo")
        if not sub or sub not in SUB: sem.append(q["id"]); continue
        a = ASS[SUB[sub]["assunto_codigo"]]; m = MAT[a["materia_codigo"]]
        q.update({"area_codigo": m["area_codigo"], "materia_codigo": m["codigo"], "assunto_codigo": a["codigo"], "subassunto_codigo": sub})
        cont["plataforma" if q["id"] in ja else "classificação"] += 1
        q.setdefault("tipo_prova", "oficial")   # questoes antigas: todas de prova oficial (ENEM, SSA, FPS)
    json.dump(lista, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(dict(cont), "sem classificação:", len(sem), sem[:30])
json.dump(sem, open(os.path.join(R, "unificacao", "sem_classificacao.json"), "w"))
