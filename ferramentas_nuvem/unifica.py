# Fase 2 do banco unificado: junta o banco antigo (Banco-de-questoes, com comentarios) com as questoes novas prontas.
# Para cada questao antiga acha a mesma questao no banco novo e decide qual EXTRACAO fica (o comentario antigo fica
# sempre). Tambem acha as repeticoes dentro do banco novo (simulado/apostila que copia prova oficial).
# Uso: python3 ferramentas_nuvem/unifica.py        Saida: unificacao/pares.json, unificacao/novas.json, unificacao/resumo.md
import json, glob, re, os, unicodedata, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTIGO = "/home/user/banco-de-questoes/final/banco_mapa_final.json"
RAIZES = [os.path.join(R, "_banco", "questoes"), "/home/user/banco-simulados/questoes", "/home/user/banco-vestibulares/questoes",
          "/home/user/banco-demais/questoes"]
CAT = {r["id"]: r for r in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
FORA = set(re.findall(r"^(P\d{4})", open(os.path.join(R, "docs", "lotes", "fora_do_banco.txt")).read(), re.M))
# provas com texto embaralhado sem alerta (fonte cifrada): nao contam como prontas
FORA |= set(re.findall(r"^(P\d{4})", open(os.path.join(R, "docs", "lotes", "fora_das_prontas.txt")).read(), re.M))
# gabarito so de resolucao (nao confirmado): fora da primeira carga
FORA |= set(re.findall(r"^(P\d{4})", open(os.path.join(R, "docs", "lotes", "gabarito_nao_confirmado.txt")).read(), re.M))


def gab_oficial(pid):
    """o gabarito da prova veio de arquivo de gabarito oficial (nao de resolucao / comentado)"""
    f = glob.glob(f"/home/user/*/questoes/*/*/{pid}/questoes.json") + glob.glob(os.path.join(R, "_banco", "questoes", "*", "*", pid, "questoes.json"))
    orig = json.load(open(f[0], encoding="utf-8"))[0].get("gabarito_origem") or []
    def com(g):
        a = (CAT[g]["arquivo"] or "").lower()
        return (not re.search(r"sem\s+coment", a)) and (bool(re.search(r"coment|resolu|respostas", a)) or CAT[g].get("papel") == "resolucao")
    return any(g in CAT and not com(g) for g in orig)
OUT = os.path.join(R, "unificacao"); os.makedirs(OUT, exist_ok=True)
_dp = os.path.join(OUT, "decisoes_matheus.json")
DECISOES = json.load(open(_dp, encoding="utf-8")) if os.path.exists(_dp) else {}


def palavras(s):
    s = re.sub(r"\{\{[^}]*\}\}|\\\(|\\\)|<[^>]+>|\*", " ", s or "")
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).split()


def trigramas(w): return set(zip(w, w[1:], w[2:]))


def prioridade(pid):
    """prova oficial (0) vale mais que compilacao/apostila (1) e simulado (2)"""
    g = CAT[pid]["grupo"] or ""
    return 2 if g.startswith("SIMULADO") else 1 if g in ("COMPILACAO", "APOSTILA", "ENCCEJA") else 0


# 1. questoes novas prontas: objetivas, gabarito, alternativas completas, nenhum alerta
novas = {}
for r in RAIZES:
    for f in glob.glob(r + "/*/*/*/questoes.json"):
        pid = f.split("/")[-2]
        if pid in FORA: continue
        _tb = os.path.join(os.path.dirname(f), "textos_base.json")
        # texto-base com alerta (tabela/mapa mal transcrito, trecho desenhado...) tambem tira a questao das prontas
        tb_alerta = {t["id"] for t in json.load(open(_tb, encoding="utf-8")) if t.get("alertas")} if os.path.exists(_tb) else set()
        for q in json.load(open(f, encoding="utf-8")):
            if set(q.get("textos_base_ids") or []) & tb_alerta: continue
            if q.get("formato") == "discursiva" or q.get("alertas") or not (q.get("gabarito") or q.get("anulada")) or len(q["alternativas"]) < 4:
                continue
            w = palavras(q["enunciado"] + " " + " ".join(a["texto"] for a in q["alternativas"]))
            novas[q["id"]] = {"pid": pid, "vest": q["vestibular"], "ano": q["ano"], "gab": q["gabarito"], "nimg": len(q["imagens"]),
                              "nalt": len(q["alternativas"]), "tri": trigramas(w), "w": w, "arquivo": os.path.relpath(f, "/home/user")}
print(len(novas), "questões novas prontas (objetivas)", flush=True)
idx = collections.defaultdict(set)
for qid, n in novas.items():
    w = n["w"]
    for i in range(0, max(1, len(w) - 7), 4): idx[tuple(w[i:i + 8])].add(qid)


def parecidas(w, excluir=()):
    cand = collections.Counter()
    for i in range(len(w) - 7):
        for qid in idx.get(tuple(w[i:i + 8]), ()):
            if qid not in excluir: cand[qid] += 1
    t = trigramas(w); out = []
    for qid, _ in cand.most_common(8):
        sn = novas[qid]["tri"]; out.append((len(t & sn) / max(1, len(t | sn)), qid))
    return sorted(out, reverse=True)


# 2. repeticoes dentro do banco novo: fica a de prova oficial (ou a primeira), as outras viram "copia_de"
copia_de = {}
for qid in sorted(novas, key=lambda q: (prioridade(novas[q]["pid"]), q)):
    if qid in copia_de: continue
    for s, outro in parecidas(novas[qid]["w"], excluir={qid}):
        if s >= 0.85 and outro not in copia_de and novas[outro]["gab"] == novas[qid]["gab"] \
                and prioridade(novas[outro]["pid"]) >= prioridade(novas[qid]["pid"]):
            copia_de[outro] = qid
print(len(copia_de), "repetições dentro do banco novo", flush=True)

# 3. antigo x novo
antigas = json.load(open(ANTIGO, encoding="utf-8"))
pares = []; usadas = set()
for o in antigas:
    w = palavras(o["statement"] + " " + " ".join(a["texto"] for a in o.get("alternativas", [])))
    cands = [(s, q) for s, q in parecidas(w) if s >= 0.5]
    # entre as parecidas, a de mesmo vestibular e ano, prova oficial, mais parecida
    cands.sort(key=lambda sq: (-(novas[sq[1]]["vest"] == o["exam"]), -(novas[sq[1]]["ano"] == str(o["ano"])),
                               prioridade(novas[sq[1]]["pid"]), -sq[0]))
    if not cands:
        pares.append({"antiga": o["id"], "nova": None, "decisao": "antiga", "motivo": "não está no banco novo pronto", "exam": o["exam"]}); continue
    s, qid = cands[0]; n = novas[qid]
    qid_final = copia_de.get(qid, qid)
    figs_antiga = [i for i in o.get("imagens", []) if "contexto" not in i]
    motivo = []
    if (o.get("gabarito") or "").strip().upper() != (n["gab"] or "").strip().upper() and prioridade(novas[qid_final]["pid"]) == 2:
        # a nova e de simulado: simulado costuma trocar a ordem das alternativas; o comentario antigo cita letras
        dec = "antiga"; motivo.append(f"gabaritos diferentes e a nova é de simulado (antiga {o.get('gabarito')}, nova {n['gab']})")
    elif (o.get("gabarito") or "").strip().upper() != (n["gab"] or "").strip().upper() and gab_oficial(novas[qid_final]["pid"]):
        # conferido em 30/09/2026 no gabarito oficial (ENEM e SSA definitivo): o do banco antigo estava errado.
        # Fica a nova com o gabarito oficial; o comentario antigo explica a resposta errada -> refazer
        dec = "nova"; motivo.append(f"gabarito oficial ({n['gab']}) diferente do antigo ({o.get('gabarito')}): comentário a refazer")
    elif (o.get("gabarito") or "").strip().upper() != (n["gab"] or "").strip().upper():
        dec = "duvida"; motivo.append(f"gabaritos diferentes (antiga {o.get('gabarito')}, nova {n['gab']})")
    elif figs_antiga and n["nimg"] == 0:
        dec = "duvida"; motivo.append("a antiga tem figura e a nova não")
    elif len(o.get("alternativas", [])) != n["nalt"]:
        dec = "duvida"; motivo.append(f"número de alternativas diferente ({len(o.get('alternativas', []))} x {n['nalt']})")
    else:
        dec = "nova"
        motivo.append("mesma questão e mesmo gabarito; a nova é cópia fiel do PDF, sem nenhum alerta")
        if any("contexto" in i for i in o.get("imagens", [])): motivo.append("a antiga usa recorte da página")
        if re.match(r"^\s*\d{1,3}\s*[.)]", o["statement"]): motivo.append("a antiga tem o número no enunciado")
    if str(o["id"]) in DECISOES:      # escolha do Matheus na pagina de pares vale mais que qualquer regra
        esc_ = DECISOES[str(o["id"])]["escolha"]
        dec = {"nova": "nova", "antiga": "antiga", "nenhuma": "antiga"}[esc_]; motivo = [f"escolha do Matheus ({esc_})"]
    pares.append({"antiga": o["id"], "nova": qid_final, "semelhanca": round(s, 3), "decisao": dec, "motivo": "; ".join(motivo),
                  "exam": o["exam"], "prova_antiga": o["prova"], "numero_antiga": o["number"], "prova_nova": novas[qid_final]["pid"]})
    if not (str(o["id"]) in DECISOES and DECISOES[str(o["id"])]["escolha"] == "nenhuma"): usadas.add(qid_final)

# 4. o que entra como questao nova: prontas que nao sao copia e nao casaram com antiga
entram = sorted(q for q in novas if q not in copia_de and q not in usadas)
json.dump(pares, open(os.path.join(OUT, "pares.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump({"entram_como_novas": entram, "copia_de": copia_de}, open(os.path.join(OUT, "novas.json"), "w", encoding="utf-8"), ensure_ascii=False)
c = collections.Counter(p["decisao"] for p in pares); ce = collections.Counter((p.get("exam"), p["decisao"]) for p in pares)
mot = collections.Counter(p["motivo"].split(" (")[0] for p in pares if p["decisao"] == "duvida")
L = ["# Junção do banco antigo com o novo (Fase 2)", "",
     f"* Questões novas prontas (objetivas): {len(novas)}",
     f"* Repetições dentro do banco novo (simulado/apostila copiando prova): {len(copia_de)} (fica a da prova oficial)",
     f"* Questões antigas: {len(antigas)} — fica a extração nova em {c['nova']}, fica a antiga em {c['antiga']}, dúvida em {c['duvida']}",
     f"* Entram como questões novas: {len(entram)}",
     f"* **Total do banco depois da junção: {len(antigas) + len(entram)}**", "", "## Por vestibular (antigas)", ""]
L += [f"* {e} — {d}: {n}" for (e, d), n in sorted(ce.items(), key=lambda t: (str(t[0][0]), t[0][1]))]
L += ["", "## Motivos das dúvidas", ""] + [f"* {m}: {n}" for m, n in mot.most_common()]
open(os.path.join(OUT, "resumo.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
