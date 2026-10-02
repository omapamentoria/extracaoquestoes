# OCR (tesseract, portugues) das provas com texto ruim no PDF (digitalizadas ou com fonte sem traducao).
# Gera ~/mnt/BM/_ocr/<PID>.pdf: cada pagina renderizada a 300 dpi com uma camada de texto invisivel do tesseract.
# O 06_extrair.py usa esse arquivo no lugar do original quando ele existe (e marca todas as questoes para conferir).
# Uso: python3 ferramentas_nuvem/ocr_pdf.py PID...      (PAR=4: provas em paralelo, 1 nucleo cada)
import json, os, re, sys, subprocess, tempfile, shutil, concurrent.futures as cf
import cv2, numpy as np

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM = os.path.expanduser("~/mnt/BM")
CAT = {d["id"]: d for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
SAIDA = os.path.join(BM, "_ocr")
DPI = 300


def fundo_branco(arq):
    """papel digitalizado fica cinza (~235): o extrator veria "tinta" na pagina toda. Divide pelo tom do papel
    (mediana) e o que fica quase branco vira branco; texto e desenho nao mudam."""
    im = cv2.imread(arq, cv2.IMREAD_GRAYSCALE)
    bg = float(np.median(im))
    if bg >= 250 or bg < 150: return
    im = np.clip(im.astype(np.float32) * 255.0 / bg, 0, 255)
    im[im > 235] = 255
    cv2.imwrite(arq, im.astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])


def bolinhas(arq):
    """letra branca dentro de circulo preto (alternativas do ENEM): o tesseract nao le. Devolve as caixas. Troca so o circulo por
    letra preta em fundo branco; nada mais da pagina muda. Circulo = componente redondo com um buraco (a letra) e
    SEM tinta colada dos lados (o "Q" e o "O" em negrito de QUESTAO tem letras vizinhas coladas)."""
    im = cv2.imread(arq, cv2.IMREAD_GRAYSCALE)
    bw = (im < 128).astype(np.uint8)
    n = 0; caixas = []
    # fechamento 5x5: o circulo pode sair partido pela letra branca (componente nao seria redondo)
    fech = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    for c in cv2.findContours(fech, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, w, h = cv2.boundingRect(c)
        if not (28 <= w <= 90 and 0.85 <= w / h <= 1.18): continue
        a = cv2.contourArea(c)
        if not 0.68 <= a / (w * h) <= 0.85: continue            # circulo (quadrado cheio da ~1)
        m = np.zeros((h, w), np.uint8); cv2.drawContours(m, [c - [x, y]], -1, 1, -1)
        reg = im[y:y + h, x:x + w]
        buraco = int(((reg >= 128) & (m == 1)).sum())
        if not 0.15 * a <= buraco <= 0.6 * a: continue           # tem uma letra branca dentro
        g = int(0.4 * w); y0, y1 = y + h // 4, y + 3 * h // 4
        if bw[y0:y1, max(0, x - g):x].any() or bw[y0:y1, x + w:x + w + g].any(): continue   # letra de palavra
        letra = (cv2.erode(m, np.ones((5, 5), np.uint8)) == 1) & (reg >= 150)   # letra = branco longe da borda do circulo
        reg[m == 1] = 255; reg[letra] = 0
        if y >= 2 and x >= 2:                                        # contorno cinza (antisserrilhado) do circulo
            mb = np.pad(m, 2); anel = (cv2.dilate(mb, np.ones((5, 5), np.uint8)) == 1) & (mb == 0)
            jan = im[y - 2:y + h + 2, x - 2:x + w + 2]
            jan[anel[:jan.shape[0], :jan.shape[1]]] = 255
        # a letra e lida sozinha (1 caractere, so A-E); "?" se o tesseract nao le
        pad = 12; crop = np.full((h + 2 * pad, w + 2 * pad), 255, np.uint8); crop[pad:pad + h, pad:pad + w] = reg
        tmp_c = arq[:-4] + f"_b{n}.png"; cv2.imwrite(tmp_c, crop)
        le = subprocess.run(["tesseract", tmp_c, "-", "--psm", "10", "-c", "tessedit_char_whitelist=ABCDE"],
                            capture_output=True, text=True, env=dict(os.environ, OMP_THREAD_LIMIT="1")).stdout.strip()
        os.remove(tmp_c)
        n += 1; caixas.append([round(v * 72 / DPI, 1) for v in (x, y, x + w, y + h)] + [le if re.fullmatch(r"[A-E]", le) else "?"])
    if n: cv2.imwrite(arq, im, [cv2.IMWRITE_JPEG_QUALITY, 90])
    # letra nao lida ("?", quase sempre o B): vem da vizinha na mesma coluna ("A ? C" -> B), so se a sequencia fecha
    caixas.sort(key=lambda b: (round(b[0] / 20), b[1]))
    for _ in range(2):
        for i, b in enumerate(caixas):
            if b[4] != "?": continue
            ant = caixas[i - 1] if i and abs(caixas[i - 1][0] - b[0]) < 5 and b[1] - caixas[i - 1][3] < 80 else None
            prox = caixas[i + 1] if i + 1 < len(caixas) and abs(caixas[i + 1][0] - b[0]) < 5 and caixas[i + 1][1] - b[3] < 80 else None
            pa, pp = (ant[4] if ant else "?"), (prox[4] if prox else "?")
            if pa in "ABCD" and pa != "?" and (pp == "?" or ord(pp) == ord(pa) + 2): b[4] = chr(ord(pa) + 1)
            elif pp in "BCDE" and pp != "?" and (pa == "?" or ord(pp) == ord(pa) + 2): b[4] = chr(ord(pp) - 1)
    return caixas


def ocr(pid):
    alvo = os.path.join(SAIDA, pid + ".pdf")
    if os.path.exists(alvo): return pid, "ja existe"
    pdf = os.path.join(BM, CAT[pid]["caminho"])
    tmp = tempfile.mkdtemp(prefix=f"ocr_{pid}_")
    try:
        # jpeg (qualidade 90): o PDF de saida fica ~10x menor que com png, sem perda visivel no texto
        subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", "-jpeg", "-jpegopt", "quality=90", pdf, os.path.join(tmp, "p")],
                       check=True, capture_output=True)
        pags = sorted(f for f in os.listdir(tmp) if f.endswith(".jpg"))
        env = dict(os.environ, OMP_THREAD_LIMIT="1")
        saidas = []; bolhas = {}
        for k, f in enumerate(pags):
            base = os.path.join(tmp, f[:-4])
            fundo_branco(os.path.join(tmp, f))
            cx = bolinhas(os.path.join(tmp, f))
            if cx: bolhas[k + 1] = cx
            subprocess.run(["tesseract", os.path.join(tmp, f), base, "-l", "por", "--dpi", str(DPI), "pdf"],
                           check=True, capture_output=True, env=env, timeout=600)
            saidas.append(base + ".pdf")
        os.makedirs(SAIDA, exist_ok=True)
        subprocess.run(["pdfunite", *saidas, alvo + ".part"], check=True, capture_output=True)
        # posicao das bolinhas (em pt, por pagina): o 06_extrair.py usa para saber que a letra ali e alternativa
        json.dump(bolhas, open(os.path.join(SAIDA, pid + ".bolhas.json"), "w"))
        os.replace(alvo + ".part", alvo)
        return pid, f"{len(pags)} paginas"
    except Exception as e:
        return pid, "ERRO " + repr(e)[:200]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    with cf.ThreadPoolExecutor(int(os.environ.get("PAR", "4"))) as ex:
        for pid, r in ex.map(ocr, sys.argv[1:]):
            print(pid, r, flush=True)
