# Repescagem final: tenta de novo, com o codigo atual, as provas de docs/lotes/para_ocr.md que NAO sao de texto ruim
# (falharam por erro de codigo depois corrigido). A que passar vai para o repositorio da sua fase e sai da lista.
# Uso: python3 ferramentas_nuvem/refaz_lista.py [disc]   (disc: so as provas discursivas, com o gabarito discursivo)
import json, os, re, glob, subprocess, shutil, time, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(R, "_banco")
CAT = {r["id"]: r for r in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
OCR_P = os.path.join(R, "docs", "lotes", "para_ocr.md")
DEST = {"ENEM": None, "SSA": None, "SIMULADO_ENEM": "/home/user/banco-simulados", "SIMULADO_SSA": "/home/user/banco-simulados",
        "DEMAIS": "/home/user/banco-demais"}
for g in ("FUVEST", "UNICAMP", "UERJ", "UNESP", "SIMULADO_FUVEST", "SIMULADO_UERJ", "SIMULADO_UNESP", "SIMULADO_UNICAMP"):
    DEST[g] = "/home/user/banco-vestibulares"
def git(*a, cwd):
    return subprocess.run(["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", *a], cwd=cwd, capture_output=True, text=True)
linhas = open(OCR_P, encoding="utf-8").read().split("\n")
# prova discursiva (2a fase, "exame discursivo", respostas): o extrator e de multipla escolha -> fica para depois
DISC = re.compile(r"(?i)2.? ?fase|segunda fase|discursiv|dissertativ|\bresp\b|resp\.pdf|reda[çc][ãa]o")
MODO_DISC = len(sys.argv) > 1 and sys.argv[1] == "disc"
NOME = "disc" if MODO_DISC else "repesca"
pids = [m.group(1) for l in linhas for m in [re.match(r"\* (P\d{4}) — ", l)] if m and "texto:" not in l and "embaralhado" not in l
        and CAT.get(m.group(1), {}).get("grupo") in DEST
        and bool(DISC.search(" ".join(CAT[m.group(1)].get(k) or "" for k in ("arquivo", "conjunto", "fase_etapa")))) == MODO_DISC]
print(len(pids), "provas para tentar de novo", flush=True)
for i in range(0, len(pids), 10):
    lote = pids[i:i + 10]
    subprocess.run([sys.executable, os.path.join(R, "ferramentas_nuvem", "lote.py"), f"{NOME}{i // 10 + 1:02d}", *lote],
                   env=dict(os.environ, PAR="4"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok, repos = [], set()
    for pid in lote:
        r = CAT[pid]; d = glob.glob(f"{B}/questoes/*/*/{pid}")
        if not d or not os.path.exists(d[0] + "/questoes.json"): continue
        q = json.load(open(d[0] + "/questoes.json")); n = len(q)
        n_pend = sum(1 for x in q if any("PENDENTE" in a for a in x.get("alertas", [])))
        esp = int(r["questoes_estimadas"]) if str(r.get("questoes_estimadas") or "").isdigit() else None
        pags = int(r["paginas"]) if str(r.get("paginas") or "").isdigit() else 0
        falhou = (esp and n < 0.5 * esp) or (not esp and pags >= 8 and n < pags) or (n >= 10 and n_pend > 0.5 * n) or n == 0
        if falhou: shutil.rmtree(d[0]); continue
        dest = DEST[r["grupo"]]
        if dest:
            novo = os.path.join(dest, "questoes", os.path.relpath(d[0], os.path.join(B, "questoes")))
            if os.path.exists(novo): shutil.rmtree(novo)
            os.makedirs(os.path.dirname(novo), exist_ok=True); shutil.move(d[0], novo)
            rv = os.path.join(novo, "revisao")
            if os.path.isdir(rv): shutil.rmtree(rv)
            repos.add(dest)
        else:
            git("add", "-f", os.path.relpath(d[0], R), cwd=R)
        ok.append(pid)
    if ok:
        linhas = [l for l in linhas if not any(l.startswith(f"* {p} — ") for p in ok)]
        open(OCR_P, "w", encoding="utf-8").write("\n".join(linhas))
    msg = f"{'Discursivas' if MODO_DISC else 'Repescagem'}: {len(ok)} de {len(lote)} provas recuperadas ({', '.join(ok)})\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01QbmqnpCJdDCit6kkZUyzUQ"
    for repo in sorted(repos) + [R]:
        git("add", "-A", "." if repo != R else "docs", cwd=repo); git("commit", "-q", "-m", msg, cwd=repo)
        for k in range(5):
            if git("push", "-q", "-u", "origin", "claude/magical-edison-fi62ix", cwd=repo).returncode == 0: break
            time.sleep(2 ** (k + 1))
    print(f"{NOME}{i // 10 + 1:02d}: {len(ok)} de {len(lote)} recuperadas", flush=True)
print("REPESCAGEM CONCLUIDA", flush=True)
