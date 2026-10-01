# Fase 3 do banco unificado: gera o banco no formato da plataforma (repositorio Banco-de-questoes, final/partes).
# - questoes antigas: continuam no MESMO arquivo de parte, com o mesmo id e o mesmo comentario; quando a junção decidiu
#   "nova", o texto, as alternativas, as imagens e o gabarito (oficial) vem da extracao nova;
# - comentario de questao antiga cujo gabarito antigo estava errado: sai (guardado em final/comentarios_a_refazer.json);
# - questoes novas: ids a partir de 100001 (fixos, unificacao/ids_novos.json), em banco_parte_07.json em diante;
# - texto-base ligado a questao vai junto no enunciado (a plataforma mostra uma questao por vez);
# - imagens para web: largura maxima 1000 px, WebP, em imagens/.
# - resolucao comentada feita pelo Gemini (ramo comentarios-gemini), so a que passou no confere_comentarios.py:
#   entra na questao que esta sem comentario (novas e as de comentario retirado). Informe a pasta em COMENTARIOS=.
# Uso: [COMENTARIOS=<pasta do ramo comentarios-gemini>] python3 ferramentas_nuvem/converte.py <pasta do repositorio Banco-de-questoes>
import json, os, sys, glob, re, collections, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from confere_comentarios import carrega as carrega_comentarios

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = sys.argv[1]
CAT = {d["id"]: d for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
RAIZES = [os.path.join(R, "_banco", "questoes"), "/home/user/banco-simulados/questoes", "/home/user/banco-vestibulares/questoes",
          "/home/user/banco-demais/questoes"]
pares = json.load(open(os.path.join(R, "unificacao", "pares.json"), encoding="utf-8"))
entram = json.load(open(os.path.join(R, "unificacao", "novas.json"), encoding="utf-8"))["entram_como_novas"]
MAPA_IDS = os.path.join(R, "unificacao", "ids_novos.json")
ids_novos = json.load(open(MAPA_IDS)) if os.path.exists(MAPA_IDS) else {}
COMENT = carrega_comentarios(os.environ["COMENTARIOS"])[0] if os.environ.get("COMENTARIOS") else {}


def comentario(qid, gab):
    """comentario aceito do Gemini, so se foi escrito para o gabarito que a questao tem hoje"""
    c = COMENT.get(qid)
    return {k: v for k, v in c.items() if k != "_gabarito"} if c and c["_gabarito"] == gab else None
IMG_DIR = os.path.join(DEST, "imagens"); os.makedirs(IMG_DIR, exist_ok=True)

# 1. carrega as questoes novas usadas (e os textos-base da prova)
precisa = set(entram) | {p["nova"] for p in pares if p["decisao"] == "nova"}
novas, bases, pasta_de = {}, {}, {}
for r in RAIZES:
    for f in glob.glob(r + "/*/*/*/questoes.json"):
        d = os.path.dirname(f); pid = d.split("/")[-1]
        qs = [q for q in json.load(open(f, encoding="utf-8")) if q["id"] in precisa]
        if not qs: continue
        tb = os.path.join(d, "textos_base.json")
        if os.path.exists(tb): bases.update({t["id"]: t for t in json.load(open(tb, encoding="utf-8"))})
        for q in qs: novas[q["id"]] = q; pasta_de[q["id"]] = d
faltam = precisa - set(novas)
assert not faltam, f"questões não encontradas: {sorted(faltam)[:5]}"


def imagem_web(orig, nome):
    alvo = os.path.join(IMG_DIR, nome)
    if not os.path.exists(alvo):
        im = cv2.imread(orig, cv2.IMREAD_UNCHANGED)
        if im is None: return None
        if im.ndim == 3 and im.shape[2] == 4:          # transparencia -> fundo branco
            a = im[:, :, 3:4] / 255.0; im = (im[:, :, :3] * a + 255 * (1 - a)).astype("uint8")
        if im.shape[1] > 1000: im = cv2.resize(im, (1000, max(1, int(im.shape[0] * 1000 / im.shape[1]))), interpolation=cv2.INTER_AREA)
        cv2.imwrite(alvo, im, [cv2.IMWRITE_WEBP_QUALITY, 85])
    return nome


def monta(q, prefixo):
    """enunciado com o(s) texto(s)-base na frente; imagens e fontes renumeradas numa lista so"""
    d = pasta_de[q["id"]]
    partes = [bases[b] for b in (q.get("textos_base_ids") or []) if b in bases] + [q]
    imgs, fontes, blocos = [], [], {}
    for k, p in enumerate(partes):
        mapa_i, mapa_f = {}, {}
        for im in p.get("imagens", []):
            nome = imagem_web(os.path.join(d, im["arquivo"]), f"{prefixo}_{len(imgs) + 1}.webp")
            if nome: imgs.append(nome); mapa_i[str(im["id"])] = len(imgs)
        for j, fo in enumerate(p.get("fontes", []), 1):
            fontes.append(fo); mapa_f[str(j)] = len(fontes)
        sub = lambda t: re.sub(r"\{\{fonte:(\d+)\}\}", lambda m: "{{fonte:%s}}" % mapa_f.get(m.group(1), m.group(1)),
                               re.sub(r"\{\{img:(\d+)\}\}", lambda m: "{{img:%s}}" % mapa_i.get(m.group(1), m.group(1)), t or ""))
        blocos[k] = sub
    texto = "\n\n".join(blocos[k](p.get("texto") if k < len(partes) - 1 else p["enunciado"]) for k, p in enumerate(partes))
    ult = blocos[len(partes) - 1]
    alts = [{"letra": a["letra"], "texto": ult(a["texto"])} for a in q["alternativas"]]
    return texto.strip(), alts, ult(q.get("apos_alternativas", "")), fontes, imgs


# 2. questoes antigas: atualiza dentro do mesmo arquivo de parte
dec = {p["antiga"]: p for p in pares}
ORIG = {o["id"]: o for o in json.load(open(os.path.join(DEST, "final", "banco_mapa_final.json"), encoding="utf-8"))}   # banco antigo intacto
_rf = os.path.join(DEST, "final", "comentarios_a_refazer.json")
refazer = json.load(open(_rf, encoding="utf-8")) if os.path.exists(_rf) else {}   # rodar de novo nao apaga os ja retirados
n_coment = 0
n_restauradas = 0
n_trocadas = 0
arqs_partes = sorted(glob.glob(os.path.join(DEST, "final", "partes", "banco_parte_*.json")))
antigos = [a for a in arqs_partes if int(re.search(r"(\d+)\.json$", a).group(1)) <= 6]
for arq in antigos:
    lista = json.load(open(arq, encoding="utf-8"))
    for o in lista:
        if not o.get("analise_correta_texto") and comentario(o["id"], o.get("gabarito")):
            o.update(comentario(o["id"], o.get("gabarito"))); n_coment += 1
        p = dec.get(o["id"])
        if (not p or p["decisao"] != "nova") and o.get("origem_texto") and o["id"] in ORIG:
            # a decisao voltou para a antiga (ex.: extracao nova saiu da carga): restaura o texto e as imagens antigos
            a = ORIG[o["id"]]
            for k in ("statement", "alternativas", "imagens", "tem_imagem"): o[k] = a.get(k)
            for k in ("apos_alternativas", "fontes", "formato", "origem_texto"): o.pop(k, None)
            n_restauradas += 1
        if not p or p["decisao"] != "nova": continue
        q = novas[p["nova"]]
        texto, alts, apos, fontes, imgs = monta(q, f"{o['id']}_n")
        o.update({"statement": texto, "alternativas": alts, "apos_alternativas": apos, "fontes": fontes,
                  "imagens": imgs, "tem_imagem": "sim" if imgs else "nao", "formato": "objetiva",
                  "origem_texto": q["id"]})
        if q.get("anulada") or (q.get("gabarito") and q["gabarito"] != o.get("gabarito")):
            # gabarito antigo errado: vale o oficial; o comentario antigo explica a resposta errada -> sai
            refazer[str(o["id"])] = {k: o.get(k) for k in ("gabarito", "passos_raciocinio", "analise_correta_titulo", "analise_correta_texto",
                                                   "analise_incorretas_intro", "analise_incorretas", "quadro_resumo", "leve_para_prova", "flashcards")}
            o["gabarito"] = "anulada" if q.get("anulada") else q["gabarito"]
            for k, v in (("passos_raciocinio", []), ("analise_correta_titulo", ""), ("analise_correta_texto", ""), ("analise_incorretas_intro", ""),
                         ("analise_incorretas", []), ("quadro_resumo", []), ("leve_para_prova", ""), ("flashcards", [])):
                o[k] = v
            o["nota_revisao"] = None
            if comentario(o["id"], o["gabarito"]): o.update(comentario(o["id"], o["gabarito"])); n_coment += 1
        n_trocadas += 1
    json.dump(lista, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(refazer, open(os.path.join(DEST, "final", "comentarios_a_refazer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 3. questoes novas
prox = max([int(v) for v in ids_novos.values()] + [100000]) + 1
ordem = sorted(entram, key=lambda i: (CAT[i.split("-")[0]]["vestibular"] or "", str(CAT[i.split("-")[0]]["ano"] or ""), i))
saida = []
for qid in ordem:
    if qid not in ids_novos: ids_novos[qid] = prox; prox += 1
    q = novas[qid]; c = CAT[qid.split("-")[0]]; nid = ids_novos[qid]
    if not (q.get("anulada") or q.get("gabarito")): continue    # anulada entra (decisao do Matheus, 01/10): a tela avisa que foi anulada
    texto, alts, apos, fontes, imgs = monta(q, str(nid))
    saida.append({"id": nid, "exam": c["vestibular"], "prova": c["arquivo"], "ano": str(c["ano"] or ""),
                  "number": q["id"].split("-", 1)[1].lstrip("Q").lstrip("0") or "0", "subject": "",
                  "tema_n1": "", "tema_n2": "", "tema_n3": "", "tema_n4": "",
                  "statement": texto, "fontes": fontes, "alternativas": alts, "apos_alternativas": apos,
                  "gabarito": "anulada" if q.get("anulada") else q["gabarito"], "tem_imagem": "sim" if imgs else "nao", "imagens": imgs, "url": "",
                  "vestibular": c["vestibular"], "edicao": c.get("edicao") or "", "dia": c.get("dia") or "", "formato": "objetiva",
                  "area_prova": q.get("area") or "", "idioma": q.get("idioma"), "origem_texto": qid,
                  "passos_raciocinio": [], "analise_correta_titulo": "", "analise_correta_texto": "", "analise_incorretas_intro": "",
                  "analise_incorretas": [], "quadro_resumo": [], "leve_para_prova": "", "flashcards": [], "nota_revisao": None})
    if comentario(nid, q["gabarito"]): saida[-1].update(comentario(nid, q["gabarito"])); n_coment += 1
json.dump(ids_novos, open(MAPA_IDS, "w"), indent=0)
for a in arqs_partes:
    if a not in antigos: os.remove(a)
for k in range(0, len(saida), 1000):
    json.dump(saida[k:k + 1000], open(os.path.join(DEST, "final", "partes", f"banco_parte_{7 + k // 1000:02d}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=0)
print(f"antigas restauradas: {n_restauradas}; antigas com texto novo: {n_trocadas}; comentários a refazer: {len(refazer)}; comentários do Gemini: {n_coment}; novas: {len(saida)}; "
      f"partes novas: {(len(saida) + 999) // 1000}; imagens em imagens/: {len(os.listdir(IMG_DIR))}")
