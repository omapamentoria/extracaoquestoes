# Resolucao comentada pelo Gemini: gera os lotes de questoes que ele vai comentar.
# Cada lote e uma pasta auto-suficiente (questoes.json + as figuras), para o Gemini ler pelo GitHub ou por anexo.
#   comentarios/lotes/lote_0000/  -> os comentarios antigos retirados (gabarito antigo errado), a refazer
#   comentarios/lotes/lote_0001/ em diante -> questoes novas, 30 por lote, na ordem do banco
# A resposta de cada lote vai em comentarios/respostas/lote_NNNN.json (ver comentarios/INSTRUCOES.md).
# Uso: python3 ferramentas_nuvem/gera_lotes_comentario.py <Banco-de-questoes (ramo claude/banco-unificado)> <pasta de saida>
import json, os, sys, glob, re, shutil

BANCO, SAIDA = sys.argv[1], sys.argv[2]
POR_LOTE = 30
partes = sorted(glob.glob(os.path.join(BANCO, "final", "partes", "banco_parte_*.json")))
num = lambda f: int(re.search(r"(\d+)\.json$", f).group(1))
refazer = json.load(open(os.path.join(BANCO, "final", "comentarios_a_refazer.json"), encoding="utf-8"))


def item(q, obs=None):
    d = {"id": q["id"], "vestibular": q.get("vestibular") or q.get("exam"), "ano": q.get("ano"), "prova": q.get("prova"),
         "numero": q.get("number"), "area_prova": q.get("area_prova") or "", "idioma": q.get("idioma"),
         "enunciado": q["statement"], "fontes": q.get("fontes") or [], "imagens": q.get("imagens") or [],
         "alternativas": q["alternativas"], "apos_alternativas": q.get("apos_alternativas") or "", "gabarito": q["gabarito"]}
    if obs: d["observacao"] = obs
    return d


lotes, fora = [[]], []
for f in partes:
    if num(f) > 6: continue
    for q in json.load(open(f, encoding="utf-8")):
        r = refazer.get(str(q["id"]))
        if not r: continue
        if q["gabarito"] not in list("ABCDE"): fora.append((q["id"], "anulada")); continue
        lotes[0].append(item(q, f"O comentário antigo defendia a letra {r['gabarito']}, mas o gabarito oficial é {q['gabarito']}. "
                                f"Escreva um comentário novo, do zero, explicando a letra {q['gabarito']}."))
novas = []
for f in partes:
    if num(f) <= 6: continue
    for q in json.load(open(f, encoding="utf-8")):
        if len(q["alternativas"]) < 4 or q["gabarito"] not in [a["letra"] for a in q["alternativas"]]:
            fora.append((q["id"], "sem alternativas ou gabarito fora das alternativas")); continue
        novas.append(item(q))
lotes += [novas[k:k + POR_LOTE] for k in range(0, len(novas), POR_LOTE)]

base = os.path.join(SAIDA, "comentarios", "lotes")
if os.path.isdir(base): shutil.rmtree(base)
for n, lote in enumerate(lotes):
    d = os.path.join(base, f"lote_{n:04d}"); os.makedirs(d)
    for q in lote:
        for im in q["imagens"]: shutil.copy(os.path.join(BANCO, "imagens", im), d)
    json.dump(lote, open(os.path.join(d, "questoes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
os.makedirs(os.path.join(SAIDA, "comentarios", "respostas"), exist_ok=True)
open(os.path.join(SAIDA, "comentarios", "respostas", ".gitkeep"), "w").close()
json.dump({"lotes": len(lotes), "questoes": sum(map(len, lotes)), "por_lote": POR_LOTE, "fora": fora},
          open(os.path.join(SAIDA, "comentarios", "lotes", "indice.json"), "w"), ensure_ascii=False, indent=1)
print(f"{len(lotes)} lotes, {sum(map(len, lotes))} questões; fora: {fora}")
