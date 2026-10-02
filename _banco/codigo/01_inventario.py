# Banco MAPA - passo 1: inventario de todos os PDFs de C:\BM
# Retomavel: roda por no maximo ORCAMENTO segundos e continua de onde parou.
# Saida: _banco/inventario.jsonl (uma linha por PDF)
import os, sys, json, time, hashlib, subprocess, re

RAIZ = os.path.expanduser("~/mnt/BM")
SAIDA = os.path.join(RAIZ, "_banco", "inventario.jsonl")
ORCAMENTO = float(sys.argv[1]) if len(sys.argv) > 1 else 150

STOP = set("""de que a o e do da em um para com não nao uma os no se na por mais as dos como mas ao das
à pelo pela ou quando muito nos já ja também tambem só so seu sua ser são sao foi há ha entre depois sem mesmo aos
isso ela ele esse essa este esta está esta pode sobre qual quais texto questão questao alternativa""".split())

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def pdfinfo(p):
    try:
        out = subprocess.run(["pdfinfo", p], capture_output=True, text=True, timeout=30, errors="replace").stdout
    except Exception as e:
        return {"erro_info": str(e)}
    d = {}
    for l in out.splitlines():
        if ":" in l:
            k, v = l.split(":", 1)
            d[k.strip()] = v.strip()
    return d

def texto(p, pg):
    try:
        return subprocess.run(["pdftotext", "-f", str(pg), "-l", str(pg), "-layout", p, "-"],
                              capture_output=True, text=True, timeout=30, errors="replace").stdout
    except Exception:
        return ""

def legib(t):
    toks = re.findall(r"[a-záéíóúâêôãõçà]+", t.lower())
    if len(toks) < 20:
        return None
    return round(sum(1 for x in toks if x in STOP) / len(toks), 3)

feitos = set()
if os.path.exists(SAIDA):
    with open(SAIDA, encoding="utf-8") as f:
        for l in f:
            try: feitos.add(json.loads(l)["caminho"])
            except Exception: pass

LISTA = os.path.join(RAIZ, "_banco", "lista_pdfs.txt")
if os.path.exists(LISTA):
    arqs = open(LISTA, encoding="utf-8").read().splitlines()
else:
    arqs = []
    for dp, dn, fn in os.walk(RAIZ):
        dn[:] = sorted(d for d in dn if d != "_banco")
        for n in sorted(fn):
            if n.lower().endswith((".pdf", ".pdf_")):
                arqs.append(os.path.relpath(os.path.join(dp, n), RAIZ))
    open(LISTA, "w", encoding="utf-8").write("\n".join(arqs))

def processa(rel):
    p = os.path.join(RAIZ, rel)
    r = {"caminho": rel, "tamanho": os.path.getsize(p)}
    try: r["md5"] = md5(p)
    except Exception as e: r["md5"] = None; r["erro"] = str(e)
    info = pdfinfo(p)
    try: npg = int(info.get("Pages", "0"))
    except ValueError: npg = 0
    r["paginas"] = npg
    r["titulo_meta"] = info.get("Title", "")
    r["produtor"] = info.get("Producer", "") or info.get("Creator", "")
    r["criptografado"] = info.get("Encrypted", "")
    if "erro_info" in info or npg == 0: r["pdf_ruim"] = True
    amostra = sorted(set(x for x in [1, 2, max(1, npg // 2)] if 1 <= x <= npg))
    chars, legs, trecho = [], [], ""
    for pg in amostra:
        t = texto(p, pg)
        chars.append(len(t.strip()))
        lg = legib(t)
        if lg is not None: legs.append(lg)
        if pg <= 2: trecho += " ".join(t.split())[:600] + " | "
    r["chars_amostra"] = chars
    r["legib"] = round(sum(legs) / len(legs), 3) if legs else None
    r["trecho"] = trecho[:1200]
    return r

if __name__ == "__main__":
    from multiprocessing import Pool
    t0 = time.time(); novos = 0
    pend = [x for x in arqs if x not in feitos]
    with Pool(2) as pool, open(SAIDA, "a", encoding="utf-8") as out:
        it = pool.imap_unordered(processa, pend)
        for r in it:
            out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush()
            novos += 1
            if time.time() - t0 > ORCAMENTO:
                pool.terminate(); break
    print(f"total PDFs: {len(arqs)} | ja feitos: {len(feitos)} | novos: {novos} | faltam: {len(arqs) - len(feitos) - novos}")
