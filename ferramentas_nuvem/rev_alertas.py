# Pagina de revisao humana das questoes COM ALERTA (so elas) das provas dadas.
# Uso: python3 ferramentas_nuvem/rev_alertas.py <pasta_saida> PID...
# Saida: <pasta>/index.html + <pasta>/dados/indice.json + <pasta>/dados/<PID>.json (recortes do PDF e figuras em
# jpeg embutido, para caber no limite de arquivos da pagina). As marcacoes (certa / tem erro + nota) ficam no banco de
# dados da pagina (colecao "revisao", um documento por questao) e o Claude le de la.
import json, os, sys, glob, base64, subprocess, tempfile, cv2, numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM = os.path.expanduser("~/mnt/BM")
CAT = {d["id"]: d for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
RAIZES = [os.path.join(R, "_banco", "questoes"), "/home/user/banco-simulados/questoes", "/home/user/banco-vestibulares/questoes",
          "/home/user/banco-demais/questoes", os.path.join(BM, "_banco", "questoes")]
out, pids = sys.argv[1], sys.argv[2:]
os.makedirs(os.path.join(out, "dados"), exist_ok=True)
TMP = tempfile.mkdtemp(prefix="rev_")


def b64(im, q=60):
    ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, q])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode() if ok else None


def figura(arq, maxw=440):
    im = cv2.imread(arq, cv2.IMREAD_GRAYSCALE)
    if im is None: return None
    if im.shape[1] > maxw: im = cv2.resize(im, (maxw, int(im.shape[0] * maxw / im.shape[1])), interpolation=cv2.INTER_AREA)
    return b64(im, 50)


def recortes(pdf, caixas, dpi=64):
    """uma imagem por pagina: a uniao das caixas da questao naquela pagina (pt), com folga"""
    res = []
    for pg, cx in sorted(caixas.items(), key=lambda t: int(t[0])):
        if not cx: continue
        x0 = max(0, min(c[0] for c in cx) - 6); y0 = max(0, min(c[1] for c in cx) - 6)
        x1 = max(c[2] for c in cx) + 6; y1 = max(c[3] for c in cx) + 6
        e = dpi / 72; base = os.path.join(TMP, "r")
        subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-f", str(pg), "-l", str(pg), "-x", str(int(x0 * e)), "-y", str(int(y0 * e)),
                        "-W", str(int((x1 - x0) * e)), "-H", str(int((y1 - y0) * e)), "-singlefile", "-png", pdf, base], capture_output=True)
        im = cv2.imread(base + ".png", cv2.IMREAD_GRAYSCALE)
        if im is not None: res.append(b64(im, 45))
    return res


indice = []
for pid in pids:
    ds = [d for r in RAIZES for d in glob.glob(f"{r}/*/*/{pid}") if os.path.exists(d + "/questoes.json")]
    if not ds: print(pid, "sem saída"); continue
    d = ds[0]; P = CAT[pid]; pdf = os.path.join(BM, P["caminho"])
    q = json.load(open(d + "/questoes.json", encoding="utf-8"))
    tb = json.load(open(d + "/textos_base.json", encoding="utf-8")) if os.path.exists(d + "/textos_base.json") else []
    sel = [x for x in q if x.get("alertas")]
    if not sel: continue
    usados = {i for x in sel for i in (x.get("textos_base_ids") or [])}
    for x in sel + [t for t in tb if t["id"] in usados]:
        for im in x.get("imagens", []):
            im["web"] = figura(os.path.join(d, im["arquivo"]))
        x["recortes_web"] = recortes(pdf, x.get("caixas") or {}) if os.path.exists(pdf) else []
        for k in ("caixas", "arquivo_origem", "gabarito_origem", "status_revisao"): x.pop(k, None)
    tit = " ".join(str(v) for v in (P["vestibular"], P["ano"], P.get("edicao") or "", ("dia " + P["dia"]) if P.get("dia") else "") if v).strip()
    ocr = any("texto lido por OCR" in a for x in sel for a in x["alertas"])
    dados = {"id": pid, "titulo": tit, "arquivo": P["arquivo"], "total": len(q), "ocr": ocr,
             "questoes": sel, "textos_base": [t for t in tb if t["id"] in usados]}
    # caractere que o PDF nao traduz (U+FFFD, ja tem alerta): marcador visivel na pagina
    open(os.path.join(out, "dados", pid + ".json"), "w", encoding="utf-8").write(json.dumps(dados, ensure_ascii=False).replace("\ufffd", "⟨?⟩"))
    indice.append({"id": pid, "titulo": tit, "grupo": P["vestibular"], "arquivo": P["arquivo"], "total": len(q), "com_alerta": len(sel),
                   "ids": [x["id"] for x in sel], "ocr": ocr})
    print(pid, len(sel), "de", len(q), "com alerta", round(os.path.getsize(os.path.join(out, "dados", pid + ".json")) / 1e6, 1), "MB", flush=True)
indice.sort(key=lambda p: (p["grupo"] or "", p["titulo"]))
json.dump(indice, open(os.path.join(out, "dados", "indice.json"), "w", encoding="utf-8"), ensure_ascii=False)
tot = sum(os.path.getsize(f) for f in glob.glob(os.path.join(out, "dados", "*")))
print(len(indice), "provas,", sum(p["com_alerta"] for p in indice), "questões,", round(tot / 1e6, 1), "MB")
import shutil
shutil.copy(os.path.join(R, "ferramentas_nuvem", "rev_alertas.html"), os.path.join(out, "index.html"))
