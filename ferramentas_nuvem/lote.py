# Roda um lote de provas na nuvem: baixa do Drive (prova + arquivos da mesma pasta),
# extrai com o 06_extrair.py (2 de cada vez) e escreve a triagem em docs/lotes/<lote>.md.
# Uso: python3 ferramentas_nuvem/lote.py <nome_lote> PID...
import json, os, re, sys, glob, subprocess, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(R, "_banco")
BM = os.path.expanduser("~/mnt/BM")
nome, pids = sys.argv[1], sys.argv[2:]
CAT = {d["id"]: d for d in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}

# 1. baixar
mapa = json.load(open(os.path.join(R, "ferramentas_nuvem", "mapa_drive.json")))
pastas = {os.path.dirname(CAT[p]["caminho"]) for p in pids}
# gabaritos/resolucoes pareados no catalogo, mesmo quando estao em outra pasta
apoio = {g for p in pids for k in ("gabarito_ids", "resolucao_ids", "padrao_ids") for g in (CAT[p].get(k) or "").split() if g in CAT}
sel = [x for x in mapa if os.path.dirname(x["path"]) in pastas or x.get("pid") in apoio]
tmp = f"/tmp/lote_{nome}.json"
json.dump(sel, open(tmp, "w"), ensure_ascii=False)
subprocess.run([sys.executable, os.path.join(R, "ferramentas_nuvem", "drive_sync.py"), "baixar", tmp, BM], check=True)

# 2. extrair
subprocess.run(["bash", os.path.join(B, "ferramentas", "roda2.sh"), *pids], cwd=B, stdout=subprocess.DEVNULL)

# 3. triagem
linhas = ["| Prova | Ano | Edição | Dia | Questões | Esperado | Faltando | Sem gabarito | PENDENTE | Com alerta | Glifos desconhecidos | Erro |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
resumo_alertas = collections.Counter()
for p in pids:
    c = CAT[p]
    log = open(f"/tmp/r_{p}.log", encoding="utf-8", errors="replace").read() if os.path.exists(f"/tmp/r_{p}.log") else ""
    erro = "sim" if re.search(r"Traceback|Error", log) else ""
    m = re.search(r"sequência de (\d+)", log)
    esperado = m.group(1) if m else (c.get("questoes_estimadas") or "?")
    falt = re.search(r"números faltando[^\n]*", log)
    d = glob.glob(f"{B}/questoes/*/*/{p}")
    if not d:
        linhas.append(f"| {p} | {c['ano']} | {c['edicao']} | {c['dia']} | 0 | {esperado} | — | — | — | — | — | {erro or 'sem saída'} |")
        continue
    q = json.load(open(d[0] + "/questoes.json"))
    sem_gab = sum(1 for x in q if not (x.get("gabarito_discursivo") if x.get("formato") == "discursiva" else x.get("gabarito")))
    pend = sum(1 for x in q if any("PENDENTE" in a for a in x.get("alertas", [])))
    com_al = sum(1 for x in q if x.get("alertas"))
    for x in q:
        for a in x.get("alertas", []):
            resumo_alertas[re.sub(r"\d+", "N", a)[:90]] += 1
    glif = len(glob.glob(d[0] + "/revisao/glifos_desconhecidos_*"))
    linhas.append(f"| {p} | {c['ano']} | {c['edicao']} | {c['dia']} | {len(q)} | {esperado} | {falt.group(0).split(':',1)[-1].strip() if falt else ''} | {sem_gab} | {pend} | {com_al} | {glif or ''} | {erro} |")

os.makedirs(os.path.join(R, "docs", "lotes"), exist_ok=True)
with open(os.path.join(R, "docs", "lotes", f"{nome}.md"), "w", encoding="utf-8") as f:
    f.write(f"# Lote {nome}\n\n" + "\n".join(linhas) + "\n\n## Alertas mais comuns\n\n")
    for a, n in resumo_alertas.most_common(25):
        f.write(f"* {n}× {a}\n")
print("\n".join(linhas))
print()
for a, n in resumo_alertas.most_common(25):
    print(f"{n:4d}  {a}")
