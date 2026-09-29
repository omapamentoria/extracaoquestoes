# Extrai uma fase inteira em lotes, sem parar: baixa, extrai (4 de cada vez), faz a triagem, marca provas que
# falharam por inteiro, apaga os PDFs do lote e grava o lote no GitHub.
# Uso: python3 ferramentas_nuvem/fase.py <prefixo_lote> <GRUPO>[,<GRUPO>...] [tamanho_lote] [repositorio_destino]
# Com repositorio_destino (ex.: /home/user/banco-simulados), as provas de cada lote saem de _banco/questoes e vao para
# <destino>/questoes/..., com a triagem em <destino>/lotes/; o commit/push do lote e feito la (e no principal, docs).
import json, os, re, sys, glob, subprocess, time, unicodedata, shutil

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(R, "_banco"); BM = os.path.expanduser("~/mnt/BM")
pref, grupos = sys.argv[1], sys.argv[2].split(",")
tam = int(sys.argv[3]) if len(sys.argv) > 3 else 10
DEST = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else None
CAT = json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))
OCR_P = os.path.join(R, "docs", "lotes", "para_ocr.md")   # provas que ficam para a etapa de visao/OCR
os.makedirs(os.path.dirname(OCR_P), exist_ok=True)
ocr_ja = set(re.findall(r"\bP\d{4}\b", open(OCR_P).read())) if os.path.exists(OCR_P) else set()

def feita(pid): return bool(glob.glob(f"{B}/questoes/*/*/{pid}/questoes.json") or (DEST and glob.glob(f"{DEST}/questoes/*/*/{pid}/questoes.json")))
fila = [r for r in CAT if r["status"] == "a extrair" and r["grupo"] in grupos]
ruins = [r for r in fila if r["texto"] != "ok" and r["id"] not in ocr_ja]
fila = [r for r in fila if r["texto"] == "ok" and r["id"] not in ocr_ja and not feita(r["id"])]
fila.sort(key=lambda r: (r["ano"] or "0", r["id"]), reverse=True)

def anota_ocr(linhas):
    novo = not os.path.exists(OCR_P)
    with open(OCR_P, "a", encoding="utf-8") as f:
        if novo: f.write("# Provas para a etapa de visão/OCR\n\nTexto ruim no catálogo ou extração que falhou por inteiro.\n\n")
        for l in linhas: f.write(l + "\n")
anota_ocr([f"* {r['id']} — {r['grupo']} {r['ano']} {r['edicao']} {r['dia']} — texto: {r['texto']} — {r['arquivo']}" for r in ruins])

def git(*a, cwd=R):
    return subprocess.run(["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", *a], cwd=cwd, capture_output=True, text=True)

n_lotes = (len(fila) + tam - 1) // tam
print(f"{len(fila)} provas em {n_lotes} lotes; {len(ruins)} de texto ruim anotadas para OCR", flush=True)
for i in range(n_lotes):
    lote = fila[i * tam:(i + 1) * tam]; nome = f"{pref}{i + 1:02d}"; pids = [r["id"] for r in lote]
    t0 = time.time(); print(f"== {nome}: {' '.join(pids)}", flush=True)
    env = dict(os.environ, PAR="4")
    subprocess.run([sys.executable, os.path.join(R, "ferramentas_nuvem", "lote.py"), nome, *pids], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # prova que falhou por inteiro (erro, nenhuma saida ou menos da metade das questoes): sai do banco e vai para OCR
    falhas = []
    for r in lote:
        d = glob.glob(f"{B}/questoes/*/*/{r['id']}")
        log = open(f"/tmp/r_{r['id']}.log", errors="replace").read() if os.path.exists(f"/tmp/r_{r['id']}.log") else ""
        m = re.search(r"sequência de (\d+)", log)
        qs_ = json.load(open(d[0] + "/questoes.json")) if d and os.path.exists(d[0] + "/questoes.json") else []
        n = len(qs_)
        n_pend = sum(1 for x in qs_ if any("PENDENTE" in a for a in x.get("alertas", [])))
        esp = int(r["questoes_estimadas"]) if str(r.get("questoes_estimadas") or "").isdigit() else None
        pags = int(r["paginas"]) if str(r.get("paginas") or "").isdigit() else 0
        motivo = ("erro no extrator" if "Traceback" in log else "nenhuma questão" if n == 0
                  else f"só {n} questões (esperado ~{esp})" if esp and n < 0.5 * esp
                  else f"só {n} questões em {pags} páginas" if not esp and pags >= 8 and n < pags
                  else f"{n_pend} de {n} questões PENDENTES (símbolos sem tradução)" if n >= 10 and n_pend > 0.5 * n else "")
        if motivo:
            falhas.append(f"* {r['id']} — {r['grupo']} {r['ano']} {r['edicao']} {r['dia']} — {motivo} — {r['arquivo']}")
            for dd in d: subprocess.run(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", os.path.relpath(dd, R)], cwd=R); subprocess.run(["rm", "-r", "--", dd])
    if falhas: anota_ocr(falhas)
    # PDFs do lote nao ficam no disco (voltam do Drive se precisar)
    mapa = json.load(open(os.path.join(R, "ferramentas_nuvem", "mapa_drive.json")))
    pastas = {os.path.dirname(r["caminho"]) for r in lote}
    for x in mapa:
        if os.path.dirname(x["path"]) in pastas:
            f_ = os.path.join(BM, x["path"])
            if os.path.isfile(f_): os.remove(f_)
    msg = (f"Extração {nome}: {len(lote) - len(falhas)} provas ({', '.join(pids)})"
           + (f"\n\nFalharam (vão para OCR): {len(falhas)}" if falhas else "")
           + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01QbmqnpCJdDCit6kkZUyzUQ")
    alvos = [R]
    if DEST:
        # provas do lote vao para o repositorio da fase
        for r in lote:
            for d in glob.glob(f"{B}/questoes/*/*/{r['id']}"):
                novo = os.path.join(DEST, "questoes", os.path.relpath(d, os.path.join(B, "questoes")))
                if os.path.exists(novo): shutil.rmtree(novo)
                os.makedirs(os.path.dirname(novo), exist_ok=True); shutil.move(d, novo)
                rv = os.path.join(novo, "revisao")
                if os.path.isdir(rv): shutil.rmtree(rv)       # recortes de conferencia nao vao para o banco
        os.makedirs(os.path.join(DEST, "lotes"), exist_ok=True)
        tri = os.path.join(R, "docs", "lotes", f"{nome}.md")
        if os.path.exists(tri): shutil.copy(tri, os.path.join(DEST, "lotes", f"{nome}.md"))
        git("add", "-A", ".", cwd=DEST); git("commit", "-q", "-m", msg, cwd=DEST); alvos.insert(0, DEST)
    git("add", "-A", "_banco/questoes", "docs")
    git("commit", "-q", "-m", msg)
    for alvo in alvos:
        for k in range(5):
            p = git("push", "-q", "-u", "origin", "claude/magical-edison-fi62ix", cwd=alvo)
            if p.returncode == 0: break
            time.sleep(2 ** (k + 1))
    print(f"   {nome} ok em {int(time.time() - t0)} s; falhas: {len(falhas)}; push: {'ok' if p.returncode == 0 else p.stderr[-200:]}", flush=True)
print("FASE CONCLUÍDA", flush=True)
