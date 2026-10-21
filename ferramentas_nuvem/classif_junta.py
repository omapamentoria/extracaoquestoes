# Fase 5b: confere as respostas da classificacao (unificacao/classif/respostas) e grava em unificacao/classificacao.json.
# Recusa o lote inteiro se os ids nao baterem; recusa a questao se o codigo nao existir. Mede o acerto no piloto
# (questoes antigas ja classificadas na plataforma).
# Uso: python3 ferramentas_nuvem/classif_junta.py [--gravar]
import json, os, sys, glob, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(R, "unificacao", "classif")
M = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
SUB = {s["codigo"]: s for s in M["subassuntos"] if s["ativo"]}
ASS = {a["codigo"]: a for a in M["assuntos"]}
MAT = {m["codigo"]: m for m in M["materias"]}
arq_cls = os.path.join(R, "unificacao", "classificacao.json")
cls = json.load(open(arq_cls, encoding="utf-8"))
piloto = json.load(open(os.path.join(C, "piloto.json")))
gold = piloto["gold"]


def cadeia(sub):
    a = ASS[SUB[sub]["assunto_codigo"]]; m = MAT[a["materia_codigo"]]
    return {"area_codigo": m["area_codigo"], "materia_codigo": m["codigo"], "assunto_codigo": a["codigo"], "subassunto_codigo": sub}


ok, ruins, conf, mudou_area = {}, [], collections.Counter(), []
acerto = collections.Counter()
for f in sorted(glob.glob(os.path.join(C, "lotes", "lote_*.json"))):
    nome = os.path.basename(f); resp_f = os.path.join(C, "respostas", nome)
    if not os.path.exists(resp_f): continue
    lote = json.load(open(f, encoding="utf-8"))
    try: resp = json.load(open(resp_f, encoding="utf-8"))
    except Exception as e: ruins.append(f"{nome}: JSON inválido"); continue
    if [r.get("id") for r in resp] != [q["id"] for q in lote]: ruins.append(f"{nome}: ids não batem"); continue
    for q, r in zip(lote, resp):
        if r.get("sub") not in SUB or r.get("conf") not in ("alta", "media", "baixa"): ruins.append(f"{nome}: {q['id']} código {r.get('sub')!r}"); continue
        c = cadeia(r["sub"]); conf[r["conf"]] += 1
        if str(q["id"]) in gold:
            g = cadeia(gold[str(q["id"])]); acerto["n"] += 1
            for k in ("area_codigo", "materia_codigo", "assunto_codigo", "subassunto_codigo"): acerto[k] += c[k] == g[k]
            continue                      # antiga ja classificada: fica a da plataforma
        if q["area"] and q["area"] != "redacao" and c["area_codigo"] != q["area"]: mudou_area.append((q["id"], q["area"], c["area_codigo"]))
        ok[str(q["id"])] = {**c, "conf": r["conf"]}
if acerto["n"]:
    print(f"piloto ({acerto['n']} já classificadas): " + ", ".join(f"{k.split('_')[0]} {100 * acerto[k] / acerto['n']:.0f}%" for k in
                                                                  ("area_codigo", "materia_codigo", "assunto_codigo", "subassunto_codigo")))
print(f"classificadas: {len(ok)}; confiança {dict(conf)}; área diferente da impressa: {len(mudou_area)}; problemas: {len(ruins)}")
for x in ruins[:20]: print("  ", x)
if "--gravar" in sys.argv:
    for i, c in ok.items():
        d = cls.setdefault(i, {}); area_antes, fonte_area = d.get("area_codigo"), d.get("fonte_area")
        d.update(c)
        d["fonte_area"] = fonte_area if fonte_area and area_antes == c["area_codigo"] else "classificação"
        d["fonte_sub"] = "IA"
    json.dump(cls, open(arq_cls, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("gravado em unificacao/classificacao.json")
