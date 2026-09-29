# Varre as provas ja extraidas e tira do banco as que falharam por inteiro (texto do PDF embaralhado, so a capa
# lida etc.): menos da metade das questoes estimadas, ou menos questoes do que paginas quando nao ha estimativa.
# Elas vao para docs/lotes/para_ocr.md. Uso: python3 ferramentas_nuvem/varre_falhas.py [--aplicar]
import json, os, sys, glob, subprocess
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(R, "_banco")
CAT = {r["id"]: r for r in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
OCR_P = os.path.join(R, "docs", "lotes", "para_ocr.md")
novas = []
for qj in sorted(glob.glob(f"{B}/questoes/*/*/*/questoes.json")):
    d = os.path.dirname(qj); pid = os.path.basename(d); r = CAT.get(pid)
    if not r: continue
    n = len(json.load(open(qj)))
    esp = int(r["questoes_estimadas"]) if str(r.get("questoes_estimadas") or "").isdigit() else None
    pags = int(r["paginas"]) if str(r.get("paginas") or "").isdigit() else 0
    motivo = (f"só {n} questões (esperado ~{esp})" if esp and n < 0.5 * esp
              else f"só {n} questões em {pags} páginas" if not esp and pags >= 8 and n < pags else "")
    if motivo:
        novas.append(f"* {pid} — {r['grupo']} {r['ano']} {r['edicao']} {r['dia']} — {motivo} — {r['arquivo']}")
        print(novas[-1])
        if "--aplicar" in sys.argv:
            subprocess.run(["git", "rm", "-r", "-q", "--cached", "--ignore-unmatch", os.path.relpath(d, R)], cwd=R)
            subprocess.run(["rm", "-r", "--", d])
if novas and "--aplicar" in sys.argv:
    with open(OCR_P, "a", encoding="utf-8") as f:
        for l in novas: f.write(l + "\n")
print(len(novas), "provas com falha")
