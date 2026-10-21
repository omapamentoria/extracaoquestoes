# Repescagem de gabarito: provas ja extraidas (em qualquer repositorio do banco) com mais da metade das questoes sem
# gabarito, mas que tem gabarito ou resolucao pareada no catalogo, sao extraidas de novo com o codigo atual (que le as
# resolucoes). Commit/push a cada 10 provas. Uso: python3 ferramentas_nuvem/refaz_gabarito.py
import json, os, glob, subprocess, shutil, time, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(R, "_banco")
CAT = {r["id"]: r for r in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
REPOS = [R, "/home/user/banco-simulados", "/home/user/banco-vestibulares", "/home/user/banco-demais"]
def git(*a, cwd):
    return subprocess.run(["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com", *a], cwd=cwd, capture_output=True, text=True)
alvo = []
for repo in REPOS:
    raiz = os.path.join(repo, "_banco", "questoes") if repo == R else os.path.join(repo, "questoes")
    for qj in glob.glob(f"{raiz}/*/*/*/questoes.json"):
        pid = os.path.basename(os.path.dirname(qj)); c = CAT.get(pid)
        if not c or not ((c.get("gabarito_ids") or "").strip() or (c.get("resolucao_ids") or "").strip()): continue
        q = json.load(open(qj))
        if q and sum(1 for x in q if not x.get("gabarito") and not x.get("anulada")) > 0.5 * len(q):
            alvo.append((repo, os.path.dirname(qj), pid))
print(len(alvo), "provas para refazer o gabarito", flush=True)
for i in range(0, len(alvo), 10):
    lote = alvo[i:i + 10]; pids = [p for _, _, p in lote]
    subprocess.run([sys.executable, os.path.join(R, "ferramentas_nuvem", "lote.py"), f"regab{i // 10 + 1:02d}", *pids],
                   env=dict(os.environ, PAR="4"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    mudou = set()
    for repo, d_antigo, pid in lote:
        novo = glob.glob(f"{B}/questoes/*/*/{pid}")
        if not novo or not os.path.exists(novo[0] + "/questoes.json"): continue
        if repo != R:      # prova de outro repositorio: a saida nova substitui a antiga la
            shutil.rmtree(d_antigo); shutil.move(novo[0], d_antigo)
            rv = os.path.join(d_antigo, "revisao")
            if os.path.isdir(rv): shutil.rmtree(rv)
        mudou.add(repo)
    for repo in mudou:
        if repo == R:
            git("add", "-u", "_banco/questoes", cwd=R)
            for _, d, _p in lote: git("add", "-f", os.path.relpath(d, R), cwd=R)
        else:
            git("add", "-A", ".", cwd=repo)
        git("add", "-A", "docs", cwd=R) if repo == R else None
        git("commit", "-q", "-m", f"Gabarito lido das resoluções: {', '.join(pids)}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01QbmqnpCJdDCit6kkZUyzUQ", cwd=repo)
        for k in range(5):
            if git("push", "-q", "-u", "origin", "claude/magical-edison-fi62ix", cwd=repo).returncode == 0: break
            time.sleep(2 ** (k + 1))
    print(f"regab{i // 10 + 1:02d} ok", flush=True)
print("REGAB CONCLUIDO", flush=True)
