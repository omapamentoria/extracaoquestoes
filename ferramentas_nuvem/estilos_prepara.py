# Fase 5c (estilos): separa as questoes do banco por subassunto, com o texto resumido (fim do enunciado = o que se pede)
# e as alternativas, para os ajudantes criarem os estilos de cada subassunto e classificarem as questoes.
# Saida: unificacao/estilos/questoes/<SUBASSUNTO>.json  [{id, vest, ano, texto, gabarito}]
# Uso: python3 ferramentas_nuvem/estilos_prepara.py <Banco-de-questoes (ramo claude/banco-unificado)>
import json, os, sys, glob, re, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, "unificacao", "estilos", "questoes"); os.makedirs(OUT, exist_ok=True)


def resumo(q):
    t = re.sub(r"\{\{img:\d+\}\}", "[figura]", q["statement"]); t = re.sub(r"\{\{fonte:\d+\}\}", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 900: t = t[:400] + " […] " + t[-450:]
    alts = " | ".join(f"{a['letra']}) " + re.sub(r"\s+", " ", re.sub(r"\{\{img:\d+\}\}", "[figura]", a["texto"]))[:90] for a in q["alternativas"])
    return t + " || " + alts


por = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(sys.argv[1], "final", "partes", "banco_parte_*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        por[q["subassunto_codigo"]].append({"id": q["id"], "vest": q.get("vestibular") or q.get("exam"), "ano": q.get("ano"),
                                            "texto": resumo(q), "gabarito": q.get("gabarito")})
for s, l in por.items():
    json.dump(l, open(os.path.join(OUT, s + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(por), "subassuntos;", sum(map(len, por.values())), "questões")
