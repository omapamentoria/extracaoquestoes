# Fase 5b: prepara a classificacao (materia > assunto > subassunto) das questoes do banco unificado.
# Gera a taxonomia da plataforma em texto e os lotes de questoes (texto resumido) que os ajudantes classificam.
#   unificacao/classif/taxonomia.txt      subassuntos ativos, agrupados por area > materia > assunto
#   unificacao/classif/lotes/lote_NNN.json  100 questoes por lote: {id, vest, ano, area, texto}
#   unificacao/classif/piloto.json        ids do piloto (questoes antigas ja classificadas na plataforma = gabarito)
# Uso: python3 ferramentas_nuvem/classif_prepara.py <Banco-de-questoes (ramo claude/banco-unificado)>
import json, os, sys, glob, re, random, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANCO = sys.argv[1]
OUT = os.path.join(R, "unificacao", "classif"); os.makedirs(os.path.join(OUT, "lotes"), exist_ok=True)
M = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
cls = json.load(open(os.path.join(R, "unificacao", "classificacao.json"), encoding="utf-8"))
POR_LOTE = 100

# taxonomia (sem Redacao: nao ha questao objetiva de redacao)
areas = {a["codigo"]: a["nome"] for a in M["areas"]}
L = ["Formato: SUBASSUNTO_CODIGO  nome do subassunto", ""]
for a in sorted(M["areas"], key=lambda x: x["ordem"]):
    if a["codigo"] == "redacao": continue
    L.append(f"# ÁREA {a['codigo']} — {a['nome']}")
    for mt in sorted((x for x in M["materias"] if x["area_codigo"] == a["codigo"]), key=lambda x: x["ordem"]):
        L.append(f"## MATÉRIA {mt['codigo']} — {mt['nome']}")
        for s in sorted((x for x in M["assuntos"] if x["materia_codigo"] == mt["codigo"] and x["ativo"]), key=lambda x: x["ordem"]):
            L.append(f"### ASSUNTO {s['codigo']} — {s['nome']}")
            L += [f"{u['codigo']}  {u['nome']}" for u in sorted((x for x in M["subassuntos"] if x["assunto_codigo"] == s["codigo"] and x["ativo"]),
                                                                key=lambda x: x["ordem"])]
    L.append("")
open(os.path.join(OUT, "taxonomia.txt"), "w", encoding="utf-8").write("\n".join(L))


def resumo(q):
    t = re.sub(r"\{\{img:\d+\}\}", "[figura]", q["statement"]); t = re.sub(r"\{\{fonte:\d+\}\}", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 1000: t = t[:550] + " […] " + t[-400:]
    alts = " | ".join(f"{a['letra']}) " + re.sub(r"\s+", " ", re.sub(r"\{\{img:\d+\}\}", "[figura]", a["texto"]))[:110] for a in q["alternativas"])
    return t + " || " + alts


ja = {q["id"]: q for q in M["questoes"]}
itens, gold = [], []
for f in sorted(glob.glob(os.path.join(BANCO, "final", "partes", "banco_parte_*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        area = (cls.get(str(q["id"])) or {}).get("area_codigo")
        it = {"id": q["id"], "vest": q.get("vestibular") or q.get("exam"), "ano": q.get("ano"), "area": area if area in areas else None,
              "texto": resumo(q)}
        if q["id"] in ja and ja[q["id"]].get("subassunto"): gold.append(it); continue     # ja classificada na plataforma
        itens.append(it)

# piloto: 300 antigas ja classificadas (para medir acerto) + 200 novas; entram nos primeiros lotes
random.seed(7)
piloto_gold = random.sample(gold, 300)
novas_p = random.sample(itens, 200)
resto = [i for i in itens if i not in novas_p]
ordem = piloto_gold + novas_p + sorted(resto, key=lambda i: (i["area"] or "zz", i["id"]))   # lotes de uma area so, quando possivel
for k in range(0, len(ordem), POR_LOTE):
    json.dump(ordem[k:k + POR_LOTE], open(os.path.join(OUT, "lotes", f"lote_{k // POR_LOTE:03d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump({"gold": {str(i["id"]): ja[i["id"]]["subassunto"] for i in piloto_gold}, "lotes_piloto": [f"lote_{k:03d}" for k in range(5)]},
          open(os.path.join(OUT, "piloto.json"), "w"), indent=0)
print(f"a classificar: {len(itens)}; já classificadas na plataforma: {len(gold)}; lotes: {(len(ordem) + POR_LOTE - 1) // POR_LOTE}",
      collections.Counter(i["area"] for i in itens))
