# Confere as resolucoes comentadas feitas pelo Gemini (ramo comentarios-gemini do Banco-de-questoes) antes de entrarem no banco.
# Regras em comentarios/INSTRUCOES.md. Uma questao so e aceita se o formato estiver certo E o texto nao defender outra
# letra alem do gabarito oficial. "discordo" / "sem_imagem" / "incompleta" ficam para revisao humana.
# Uso: python3 ferramentas_nuvem/confere_comentarios.py <pasta do ramo comentarios-gemini>   Saida: docs/comentarios-conferencia.md
import json, os, sys, glob, re, collections

CAMPOS = ("passos_raciocinio", "analise_correta_titulo", "analise_correta_texto", "analise_incorretas_intro",
          "analise_incorretas", "quadro_resumo", "leve_para_prova", "flashcards")
TAGS = {"Fato", "Conceito", "Pegadinha", "Interpretação", "Vocabulário", "Fórmula"}
STATUS_REV = {"discordo", "sem_imagem", "incompleta"}
# "gabarito B", "alternativa correta é a C", "resposta: D", "letra E"
RESP = re.compile(r"(?i)(?:gabarito|resposta(?: correta)?|alternativa correta|letra)\s*(?:é|e|:)?\s*(?:a\s+)?(?:letra\s+)?\(?([A-E])\)?(?![\wÀ-ÿ])")


def textos(c):
    yield c["analise_correta_titulo"]; yield c["analise_correta_texto"]; yield c["analise_incorretas_intro"]; yield c["leve_para_prova"]
    yield from c["passos_raciocinio"]
    for a in c["analise_incorretas"]: yield a["rotulo"]; yield a["texto"]
    for a in c["quadro_resumo"]: yield a["item"]; yield a["detalhe"]
    for a in c["flashcards"]: yield a["frente"]; yield a["verso"]


def erros_de(q, c):
    """lista de problemas de uma resposta (vazia = aceita)"""
    e = []
    if c.get("gabarito") != q["gabarito"]: return [f"gabarito {c.get('gabarito')!r} diferente do oficial {q['gabarito']}"]
    st = c.get("status")
    if st in STATUS_REV:
        if set(c) != {"id", "status", "gabarito", "motivo"} or not str(c.get("motivo") or "").strip(): e.append("campos do status de revisão")
        return e
    if st != "ok": return [f"status {st!r}"]
    if set(c) != {"id", "status", "gabarito", *CAMPOS}: return [f"campos: faltam {sorted(set(CAMPOS) - set(c))}, sobram {sorted(set(c) - {'id', 'status', 'gabarito', *CAMPOS})}"]
    try:
        p = c["passos_raciocinio"]
        if not (isinstance(p, list) and len(p) == 3 and all(isinstance(x, str) and x.strip() for x in p)): e.append("passos_raciocinio ≠ 3 frases")
        for k in ("analise_correta_titulo", "analise_correta_texto", "analise_incorretas_intro", "leve_para_prova"):
            if not (isinstance(c[k], str) and c[k].strip()): e.append(f"{k} vazio")
        if isinstance(c["analise_correta_texto"], str) and len(c["analise_correta_texto"]) < 200: e.append("analise_correta_texto curta demais")
        erradas = sorted(a["letra"] for a in q["alternativas"] if a["letra"] != q["gabarito"])
        ai = c["analise_incorretas"]
        if [a.get("alt") for a in ai] != erradas: e.append(f"analise_incorretas com letras {[a.get('alt') for a in ai]} (esperado {erradas})")
        if any(set(a) != {"alt", "rotulo", "texto"} or not a["rotulo"].strip() or not a["texto"].strip() for a in ai): e.append("analise_incorretas incompleta")
        qr = c["quadro_resumo"]
        if not (3 <= len(qr) <= 7) or any(set(a) != {"item", "detalhe"} or not a["item"].strip() or not a["detalhe"].strip() for a in qr): e.append("quadro_resumo fora do formato")
        fc = c["flashcards"]
        if not (3 <= len(fc) <= 6) or any(set(a) != {"frente", "verso", "tag"} or a["tag"] not in TAGS or not a["frente"].strip() or not a["verso"].strip() for a in fc):
            e.append("flashcards fora do formato")
        tudo = list(textos(c))
    except (KeyError, TypeError, AttributeError) as x:
        return e + [f"estrutura inválida ({x!r})"]
    j = "\n".join(tudo)
    if re.search(r"\*\*|^#|\$\$|\\\(|\\frac|\\sqrt", j, re.M): e.append("Markdown ou LaTeX no texto")
    # nenhuma frase pode apontar outra letra como resposta (fora a analise das incorretas, que fala delas)
    for t in [c["analise_correta_titulo"], c["analise_correta_texto"], c["leve_para_prova"], *c["passos_raciocinio"]]:
        outras = {m for m in RESP.findall(t) if m.upper() != q["gabarito"]}
        if outras: e.append(f"texto aponta {sorted(outras)} como resposta (gabarito {q['gabarito']})"); break
    return e


def carrega(pasta):
    """{id: comentario aceito}, lista de revisao, relatorio por lote"""
    aceitos, revisao, rel = {}, [], []
    for d in sorted(glob.glob(os.path.join(pasta, "comentarios", "lotes", "lote_*"))):
        nome = os.path.basename(d); lote = json.load(open(os.path.join(d, "questoes.json"), encoding="utf-8"))
        arq = os.path.join(pasta, "comentarios", "respostas", nome + ".json")
        if not os.path.exists(arq): rel.append((nome, "sem resposta", [])); continue
        try:
            txt = open(arq, encoding="utf-8").read().strip()
            txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt)      # colado com a cerca de codigo
            resp = json.loads(txt)
        except Exception as x:
            rel.append((nome, "JSON inválido", [repr(x)[:120]])); continue
        if not isinstance(resp, list) or [c.get("id") if isinstance(c, dict) else None for c in resp] != [q["id"] for q in lote]:
            rel.append((nome, "ids diferentes do lote (faltando, sobrando ou fora de ordem)", [])); continue
        probs = []
        for q, c in zip(lote, resp):
            er = erros_de(q, c)
            if er: probs.append(f"{q['id']}: " + "; ".join(er))
            elif c["status"] == "ok": aceitos[q["id"]] = {**{k: c[k] for k in CAMPOS}, "_gabarito": q["gabarito"]}
            else: revisao.append({"id": q["id"], "lote": nome, "status": c["status"], "gabarito": q["gabarito"], "motivo": c["motivo"]})
        rel.append((nome, "ok" if not probs else f"{len(probs)} questões recusadas", probs))
    return aceitos, revisao, rel


if __name__ == "__main__":
    R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    aceitos, revisao, rel = carrega(sys.argv[1])
    cont = collections.Counter(s if s in ("ok", "sem resposta", "JSON inválido") or s.startswith("ids") else "com recusas" for _, s, _ in rel)
    L = ["# Conferência das resoluções comentadas (Gemini)", "",
         f"Lotes: {len(rel)} — " + ", ".join(f"{k}: {v}" for k, v in cont.most_common()),
         f"Comentários aceitos: **{len(aceitos)}**. Para revisão humana (discordo / sem imagem / incompleta): **{len(revisao)}**.", "",
         "## Lotes a refazer ou corrigir", ""]
    for nome, s, probs in rel:
        if s not in ("ok", "sem resposta"):
            L.append(f"* {nome}: {s}"); L += [f"  * {p}" for p in probs[:15]] + (["  * …"] if len(probs) > 15 else [])
    L += ["", "## Revisão humana", ""] + [f"* {r['id']} ({r['lote']}, gabarito {r['gabarito']}) — {r['status']}: {r['motivo']}" for r in revisao]
    open(os.path.join(R, "docs", "comentarios-conferencia.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L[:12]))
