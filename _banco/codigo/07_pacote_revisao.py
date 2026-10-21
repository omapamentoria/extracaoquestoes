# Banco MAPA - passo 7: junta questoes extraidas + imagens (reduzidas) num pacote para a pagina de revisao
import os, sys, json, shutil, zipfile
import cv2
B = os.path.expanduser("~/mnt/BM/_banco")
CAT = {d["id"]: d for d in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
ids = sys.argv[1:]
TMP = os.path.expanduser("~/tmp_banco/pac"); shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)
dados = {"provas": []}
for pid in ids:
    P = CAT[pid]; d = os.path.join(B, "questoes", P["vestibular"], P["ano"], pid)
    Q = json.load(open(os.path.join(d, "questoes.json"), encoding="utf-8"))
    T = json.load(open(os.path.join(d, "textos_base.json"), encoding="utf-8"))
    NL = json.load(open(os.path.join(d, "textos_nao_ligados.json"), encoding="utf-8")) if os.path.exists(os.path.join(d, "textos_nao_ligados.json")) else []
    for item in Q + T:
        for im in item["imagens"]:
            src = os.path.join(d, im["arquivo"]); dst = f"{pid}_{os.path.basename(src)}"
            img = cv2.imread(src)
            if img.shape[1] > 900: img = cv2.resize(img, (900, int(img.shape[0] * 900 / img.shape[1])), interpolation=cv2.INTER_AREA)
            ok_png, png = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            ok_jpg, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if len(jpg) < 0.6 * len(png): dst = dst[:-4] + ".jpg"; open(os.path.join(TMP, dst), "wb").write(jpg.tobytes())
            else: open(os.path.join(TMP, dst), "wb").write(png.tobytes())
            im["web"] = dst
        item["recortes_web"] = []
        for r in item["recortes"]:
            dst = f"{pid}_{os.path.basename(r)}"; shutil.copy(os.path.join(d, r), os.path.join(TMP, dst)); item["recortes_web"].append(dst)
    dados["provas"].append({"id": pid, "titulo": f'{P["vestibular"]} {P["ano"]} — {P["edicao"]} — {P["fase_etapa"] or ""} {("dia " + P["dia"]) if P["dia"] else ""} {P["caderno"]}'.replace("  ", " "),
                            "arquivo": P["arquivo"], "questoes": Q, "textos_base": T, "nao_ligados": NL})
json.dump(dados, open(os.path.join(TMP, "dados.json"), "w", encoding="utf-8"), ensure_ascii=False)
z = os.path.join(B, "piloto", "pacote_revisao.zip")
with zipfile.ZipFile(z + ".tmp", "w", zipfile.ZIP_DEFLATED) as zf:
    for f in os.listdir(TMP): zf.write(os.path.join(TMP, f), f)
os.replace(z + ".tmp", z)
print(len(os.listdir(TMP)), "arquivos;", round(os.path.getsize(z) / 1e6, 1), "MB")
