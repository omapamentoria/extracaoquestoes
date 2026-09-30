# Auditoria dos gabaritos que vieram SO de resolucao / gabarito comentado (sem gabarito oficial): simulados e alguns
# vestibulares. A leitura automatica dessas resolucoes ja errou (SOMOS 2025, ENEM 2020). Para cada questao, o bloco
# "QUESTAO N" da resolucao e lido por tres caminhos independentes:
#   1) "Resposta X" / "Gabarito: X" no comeco do bloco;  2) "X) CORRETA" na explicacao;  3) "a alternativa correta e a X".
# Fica o gabarito so quando os caminhos que acharam algo concordam E batem com o gravado; se a resolucao aponta outra
# letra (com dois caminhos concordando), troca; qualquer conflito ou nada achado -> sem gabarito (sai das prontas).
# Uso: python3 ferramentas_nuvem/audita_resolucao.py [--aplicar]      Saida: docs/lotes/auditoria_resolucao.md
import json, os, re, sys, glob, subprocess, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.expanduser("~/mnt/BM")
CAT = {d["id"]: d for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
RAIZES = [os.path.join(R, "_banco", "questoes"), "/home/user/banco-simulados/questoes", "/home/user/banco-vestibulares/questoes",
          "/home/user/banco-demais/questoes"]
FORA = set(re.findall(r"^(P\d{4})", open(os.path.join(R, "docs", "lotes", "fora_do_banco.txt")).read(), re.M))
APLICAR = "--aplicar" in sys.argv
ALERTA = "sem gabarito confirmado: a resolução não confirma a resposta (conferir no gabarito oficial)"


def comentado(gid):
    a = (CAT[gid]["arquivo"] or "").lower()
    if re.search(r"sem\s+coment", a): return False
    return bool(re.search(r"coment|resolu|respostas", a)) or CAT[gid].get("papel") == "resolucao"


def respostas(texto):
    """{numero: [letras achadas por caminho, por bloco]} a partir dos blocos 'QUESTAO N' da resolucao"""
    cabs = list(re.finditer(r"(?im)^[ \t]*QUEST[ÃA]O[ \t]*0*(\d{1,3})\b", texto))
    out = collections.defaultdict(list)
    for k, m in enumerate(cabs):
        bloco = texto[m.start():cabs[k + 1].start() if k + 1 < len(cabs) else len(texto)]
        inicio = "\n".join(bloco.splitlines()[:3])
        achados = []
        m1 = re.search(r"(?i)\b(?:resposta|gabarito)(?:\s+correta)?\s*:?\s*\(?([A-E])\)?(?![A-Za-zÀ-ÿ])", inicio)
        if m1: achados.append(m1.group(1).upper())
        m2 = set(re.findall(r"\b([A-E])\)\s*[–-]?\s*CORRETA\b", bloco))
        if len(m2) == 1: achados.append(m2.pop())
        elif len(m2) > 1: achados.append("?")
        m3 = re.findall(r"(?i)alternativa\s+correta\s*(?:é|e)?\s*(?:a\s+)?\(?([A-E])\)?(?![A-Za-zÀ-ÿ])", bloco)
        if m3: achados.append(m3[0].upper())
        out[int(m.group(1))].append(achados)
    return out


mud = []; conf = 0; n_provas = 0; por_motivo = collections.Counter()
for r in RAIZES:
    for f in sorted(glob.glob(r + "/*/*/*/questoes.json")):
        pid = f.split("/")[-2]
        if pid in FORA: continue
        q = json.load(open(f, encoding="utf-8"))
        orig = [g for g in (q[0].get("gabarito_origem") or []) if g in CAT]
        if not orig or not all(comentado(g) for g in orig): continue
        res = collections.defaultdict(list)
        for g in orig:
            arq = os.path.join(RAIZ, CAT[g]["caminho"])
            if not os.path.exists(arq): continue
            t = subprocess.run(["pdftotext", "-layout", arq, "-"], capture_output=True).stdout.decode("utf-8", "replace")
            for n, v in respostas(t).items(): res[n] += v
        n_provas += 1; mudou = False
        for x in q:
            if x.get("formato") == "discursiva" or not x.get("gabarito") or x.get("anulada"): continue
            if x.get("idioma"): continue          # lingua estrangeira: tratada a parte (a resolucao numera igual as duas)
            blocos = res.get(x["numero"], [])
            letras = [l for b in blocos for l in b]
            distintas = set(letras)
            if len(blocos) == 1 and distintas == {x["gabarito"]}:
                conf += 1; continue
            if len(blocos) == 1 and len(distintas) == 1 and "?" not in distintas and len(letras) >= 2:
                novo, motivo = letras[0], "a resolução aponta outra letra (dois caminhos concordam)"
            else:
                novo = None
                motivo = ("bloco da questão não encontrado na resolução" if not blocos else
                          "mais de um bloco com o mesmo número" if len(blocos) > 1 else
                          "resposta não legível no bloco" if not letras else "caminhos discordam")
            por_motivo[motivo] += 1
            mud.append({"prova": pid, "questao": x["id"], "antes": x["gabarito"], "depois": novo, "motivo": motivo})
            x["gabarito"] = novo
            if novo is None: x["alertas"] = x.get("alertas", []) + [ALERTA]
            mudou = True
        if mudou and APLICAR: json.dump(q, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

por = collections.Counter(m["prova"] for m in mud)
L = ["# Auditoria dos gabaritos vindos só de resolução / gabarito comentado", "",
     f"Provas: {n_provas}. Gabaritos confirmados: {conf}. Trocados (a resolução aponta outra letra): {sum(1 for m in mud if m['depois'])}. "
     f"Sem gabarito confirmado (saem das prontas): {sum(1 for m in mud if not m['depois'])}.", "", "## Motivos", ""]
L += [f"* {k}: {v}" for k, v in por_motivo.most_common()] + ["", "## Por prova", ""]
for pid, n in por.most_common():
    c = CAT[pid]; ex = [m for m in mud if m["prova"] == pid]
    L.append(f"* {pid} — {c['vestibular']} {c['ano']} ({c['arquivo']}): {n} — "
             + ", ".join(f"{m['questao'].split('-', 1)[1]} {m['antes']}→{m['depois'] or '—'}" for m in ex[:10]) + (" …" if n > 10 else ""))
open(os.path.join(R, "docs", "lotes", "auditoria_resolucao.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(mud, open("/tmp/auditoria_resolucao.json", "w"), ensure_ascii=False)
print("\n".join(L[:30]))
