# Auditoria de gabarito: recalcula o gabarito de cada prova do banco com a MESMA funcao do 06_extrair.py (le_gabarito,
# com as regras atuais: gabarito oficial antes do comentado, nunca outra cor, tabela de varias cores) e compara com o
# gabarito gravado em questoes.json. Com --aplicar, grava so os gabaritos que mudaram (o resto da questao fica igual).
# Uso: python3 ferramentas_nuvem/audita_gabarito.py [--aplicar]      Saida: docs/lotes/auditoria_gabarito.md
import json, os, re, sys, glob, ast, subprocess, collections
import pdfplumber

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.expanduser("~/mnt/BM")
CAT = {d["id"]: d for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
RAIZES = [os.path.join(R, "_banco", "questoes"), "/home/user/banco-simulados/questoes", "/home/user/banco-vestibulares/questoes",
          "/home/user/banco-demais/questoes"]
FORA = set(re.findall(r"^(P\d{4})", open(os.path.join(R, "docs", "lotes", "fora_do_banco.txt")).read(), re.M))
APLICAR = "--aplicar" in sys.argv

# a funcao le_gabarito do extrator, sem rodar o resto do 06_extrair.py
src = open(os.path.join(R, "_banco", "codigo", "06_extrair.py"), encoding="utf-8").read()
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "le_gabarito")
CODIGO_FN = ast.get_source_segment(src, fn)


def gabarito_de(pid, numeros):
    ns = {"re": re, "os": os, "subprocess": subprocess, "pdfplumber": pdfplumber, "CAT": CAT, "RAIZ": RAIZ, "P": CAT[pid], "OCR": False, "PDF": os.path.join(RAIZ, CAT[pid]["caminho"])}
    exec(CODIGO_FN, ns)
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        gab, ids = ns["le_gabarito"]()
        # gabarito pareado que nao cobre as questoes: o da mesma pasta que cobre (igual ao extrator)
        cobre = lambda g: len(numeros & {k if isinstance(k, int) else k[0] for k in g}) / max(1, len(numeros))
        if numeros and cobre(gab) < 0.5:
            pasta = os.path.dirname(CAT[pid]["caminho"])
            irm = [d["id"] for d in CAT.values() if os.path.dirname(d["caminho"]) == pasta and d.get("papel") == "gabarito"
                   and d["id"] not in ids and os.path.exists(os.path.join(RAIZ, d["caminho"]))]
            melhor = max(((cobre(g_), gid_, g_) for gid_ in irm for g_ in [ns["le_gabarito"]([gid_])[0]]), default=None, key=lambda x: x[0])
            if melhor and melhor[0] >= 0.8: gab, ids = melhor[2], [melhor[1]]
    return gab, ids


mud = []; faltou = []; n_provas = 0
for r in RAIZES:
    for f in sorted(glob.glob(r + "/*/*/*/questoes.json")):
        pid = f.split("/")[-2]
        if pid in FORA: continue
        c = CAT[pid]
        ids_todos = (c.get("gabarito_ids") or "").split() + (c.get("resolucao_ids") or "").split()
        if any(not os.path.exists(os.path.join(RAIZ, CAT[g]["caminho"])) for g in ids_todos if g in CAT):
            faltou.append(pid); continue
        q = json.load(open(f, encoding="utf-8"))
        if all(x.get("formato") == "discursiva" for x in q): continue
        n_provas += 1
        try:
            gab, ids = gabarito_de(pid, {x["numero"] for x in q})
        except Exception as e:
            faltou.append(pid + " (erro " + repr(e)[:60] + ")"); continue
        # so vale mudanca que vem de arquivo de gabarito OFICIAL (a leitura de resolucao/comentado nao e confiavel)
        def _com(g_):
            a_ = (CAT[g_]["arquivo"] or "").lower()
            return (not re.search(r"sem\s+coment", a_)) and (bool(re.search(r"coment|resolu|respostas", a_)) or CAT[g_].get("papel") == "resolucao")
        ofic = [g_ for g_ in ids if g_ in CAT and not _com(g_)]
        if not ofic: continue
        ns_o = {"re": re, "os": os, "subprocess": subprocess, "pdfplumber": pdfplumber, "CAT": CAT, "RAIZ": RAIZ, "P": CAT[pid], "OCR": False, "PDF": os.path.join(RAIZ, CAT[pid]["caminho"])}
        exec(CODIGO_FN, ns_o)
        import io as _io, contextlib as _cl
        with _cl.redirect_stdout(_io.StringIO()): gab_of = ns_o["le_gabarito"](ofic)[0]
        mudou = False
        for x in q:
            if x.get("formato") == "discursiva": continue
            if x["numero"] not in gab_of and (x["numero"], x.get("idioma")) not in gab_of: continue
            g = gab.get((x["numero"], x["idioma"])) if x.get("idioma") else None
            g = g or gab.get(x["numero"])
            novo = None if (g or "").lower().startswith("anul") else g
            anul = bool(g and g.lower().startswith("anul"))
            if (novo, anul) != (x.get("gabarito"), bool(x.get("anulada"))):
                if not g and x.get("gabarito"): continue     # gabarito vindo da alternativa marcada no caderno: fica
                mud.append({"prova": pid, "questao": x["id"], "antes": x.get("gabarito") or ("anulada" if x.get("anulada") else None),
                            "depois": novo or ("anulada" if anul else None), "arquivos": ids})
                x["gabarito"], x["anulada"] = novo, anul
                x["alertas"] = [a for a in x.get("alertas", []) if a != "sem gabarito"] + ([] if (novo or anul) else ["sem gabarito"])
                mudou = True
        if mudou and APLICAR:
            json.dump(q, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

por = collections.Counter(m["prova"] for m in mud)
L = ["# Auditoria de gabarito", "", f"Provas conferidas: {n_provas}. Gabaritos que mudam com as regras novas: **{len(mud)}** em {len(por)} provas.",
     f"Provas sem os arquivos de gabarito baixados (não conferidas): {len(faltou)}.", "", "## Por prova", ""]
for pid, n in por.most_common():
    c = CAT[pid]; ex = [m for m in mud if m["prova"] == pid]
    L.append(f"* {pid} — {c['vestibular']} {c['ano']} {c.get('edicao') or ''} {c.get('dia') or ''} ({c['arquivo']}): {n} — "
             + ", ".join(f"{m['questao'].split('-', 1)[1]} {m['antes']}→{m['depois']}" for m in ex[:12]) + (" …" if n > 12 else ""))
L += ["", "## Não conferidas", ""] + [f"* {p}" for p in faltou]
open(os.path.join(R, "docs", "lotes", "auditoria_gabarito.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
json.dump(mud, open("/tmp/auditoria_gabarito.json", "w"), ensure_ascii=False)
print("\n".join(L[:40]))
