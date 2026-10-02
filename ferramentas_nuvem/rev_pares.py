# Pagina de decisao dos pares em duvida da Fase 2 (antiga x nova lado a lado; a escolha fica no banco da pagina).
# Uso: python3 ferramentas_nuvem/rev_pares.py <pasta_saida>
import json, os, sys, glob, base64, cv2
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
ANT = "/home/user/banco-de-questoes"
old = {o["id"]: o for o in json.load(open(ANT + "/final/banco_mapa_final.json", encoding="utf-8"))}
def b64(arq, maxw=520):
    im = cv2.imread(arq, cv2.IMREAD_GRAYSCALE)
    if im is None: return None
    if im.shape[1] > maxw: im = cv2.resize(im, (maxw, int(im.shape[0] * maxw / im.shape[1])), interpolation=cv2.INTER_AREA)
    ok, b = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 60]); return "data:image/jpeg;base64," + base64.b64encode(b.tobytes()).decode()
def nova(qid):
    pid = qid.split("-")[0]
    f = (glob.glob(f"/home/user/*/questoes/*/*/{pid}/questoes.json") + glob.glob(f"{R}/_banco/questoes/*/*/{pid}/questoes.json"))[0]
    q = [q for q in json.load(open(f, encoding="utf-8")) if q["id"] == qid][0]
    for im in q["imagens"]: im["web"] = b64(os.path.join(os.path.dirname(f), im["arquivo"]))
    return {k: q[k] for k in ("id", "vestibular", "ano", "numero", "enunciado", "fontes", "alternativas", "imagens", "gabarito", "apos_alternativas")}
pares = [p for p in json.load(open(R + "/unificacao/pares.json", encoding="utf-8")) if p["decisao"] == "duvida"]
dados = []
for p in pares:
    o = old[p["antiga"]]
    dados.append({"antiga": {"id": o["id"], "exam": o["exam"], "prova": o["prova"], "ano": o["ano"], "numero": o["number"],
                             "enunciado": o["statement"], "alternativas": o["alternativas"], "gabarito": o["gabarito"],
                             "imagens": [b64(os.path.join(ANT, "imagens", i)) for i in o.get("imagens", [])],
                             "comentario": o.get("analise_correta_texto", "")},
                  "nova": nova(p["nova"]), "motivo": p["motivo"], "semelhanca": p["semelhanca"]})
html = open(R + "/ferramentas_nuvem/rev_pares.html", encoding="utf-8").read()
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html.replace("/*DADOS*/[]", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")))
print(len(dados), "pares;", round(os.path.getsize(os.path.join(out, "index.html")) / 1e6, 1), "MB")
