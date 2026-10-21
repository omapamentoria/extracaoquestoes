# Revisao das questoes de confianca baixa: confere unificacao/classif/revisao/respostas e grava a decisao final
# em unificacao/classificacao.json (fonte_sub = "IA revisão"). Uso: python3 ferramentas_nuvem/classif_revisao_junta.py [--gravar]
import json, os, sys, glob, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(R, "unificacao", "classif", "revisao")
M = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
SUB = {s["codigo"]: s for s in M["subassuntos"] if s["ativo"]}; ASS = {a["codigo"]: a for a in M["assuntos"]}; MAT = {m["codigo"]: m for m in M["materias"]}
arq = os.path.join(R, "unificacao", "classificacao.json"); cls = json.load(open(arq, encoding="utf-8"))
st, ruins, conf = collections.Counter(), [], collections.Counter()
for f in sorted(glob.glob(os.path.join(C, "lotes", "rev_*.json"))):
    rf = os.path.join(C, "respostas", os.path.basename(f))
    if not os.path.exists(rf): st["lote sem resposta"] += 1; continue
    lote = json.load(open(f, encoding="utf-8"))
    try: resp = json.load(open(rf, encoding="utf-8"))
    except Exception: ruins.append(os.path.basename(f) + ": JSON inválido"); continue
    por_id = {r.get("id"): r for r in resp if isinstance(r, dict)}
    faltam = [q["id"] for q in lote if q["id"] not in por_id]
    if faltam: ruins.append(os.path.basename(f) + f": sem resposta para {faltam}")
    for q in lote:
        r = por_id.get(q["id"])
        if not r: continue
        if r.get("sub") not in SUB: ruins.append(f"{q['id']}: código {r.get('sub')!r}"); continue
        d = cls[str(q["id"])]; st["mantida" if d["subassunto_codigo"] == r["sub"] else "trocada"] += 1; conf[r.get("conf")] += 1
        if "--gravar" in sys.argv:
            a = ASS[SUB[r["sub"]]["assunto_codigo"]]; m = MAT[a["materia_codigo"]]
            if d.get("area_codigo") != m["area_codigo"]: d["fonte_area"] = "classificação"
            d.update({"area_codigo": m["area_codigo"], "materia_codigo": m["codigo"], "assunto_codigo": a["codigo"], "subassunto_codigo": r["sub"],
                      "conf": r.get("conf"), "fonte_sub": "IA revisão", "motivo": r.get("motivo", "")})
print(dict(st), "confiança após revisão:", dict(conf)); print("\n".join(ruins))
if "--gravar" in sys.argv: json.dump(cls, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("gravado")
