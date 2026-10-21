# Banco MAPA - passo 3: extrai o texto completo (pdftotext -layout) de cada PDF com questoes,
# guarda em _banco/texto/<md5>.txt.gz (paginas separadas por \f) e mede a legibilidade pagina a pagina.
# Retomavel. Saida: _banco/legibilidade.jsonl
import os, sys, json, time, gzip, re, subprocess, unicodedata
from multiprocessing import Pool
RAIZ = os.path.expanduser("~/mnt/BM"); B = os.path.join(RAIZ, "_banco")
TX = os.path.join(B, "texto"); os.makedirs(TX, exist_ok=True)
SAIDA = os.path.join(B, "legibilidade.jsonl")
ORC = float(sys.argv[1]) if len(sys.argv) > 1 else 150
STOP = set("""de que a o e do da em um para com não nao uma os no se na por mais as dos como mas ao das
à pelo pela ou quando muito nos já ja também tambem só so seu sua ser são sao foi há ha entre depois sem mesmo aos
isso ela ele esse essa este esta está pode sobre qual quais texto questão questao alternativa the of and to is in""".split())

def legib(t):
    toks = re.findall(r"[a-záéíóúâêôãõçà]+", t.lower())
    if len(toks) < 30: return None
    return sum(1 for x in toks if x in STOP) / len(toks)

def proc(item):
    cam, md5 = item
    p = os.path.join(RAIZ, cam); dst = os.path.join(TX, md5 + ".txt.gz")
    try:
        if os.path.exists(dst):
            txt = gzip.open(dst, "rt", encoding="utf-8").read()
        else:
            txt = subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
            with gzip.open(dst + ".tmp", "wt", encoding="utf-8") as f: f.write(txt)
            os.replace(dst + ".tmp", dst)
    except Exception as e:
        return {"caminho": cam, "texto": "erro", "erro": str(e)}
    pags = txt.split("\f")
    if pags and not pags[-1].strip(): pags = pags[:-1]
    n = len(pags); vazias = []; ruins = []
    for i, pg in enumerate(pags, 1):
        s = pg.strip()
        if len(s) < 80: vazias.append(i); continue
        lg = legib(s)
        if lg is not None and lg < 0.10: ruins.append(i)
    com_texto = n - len(vazias)
    if n == 0 or com_texto == 0: est = "sem_texto (imagem)"
    elif len(ruins) > 0.5 * com_texto: est = "corrompido"
    elif ruins: est = "parcialmente corrompido"
    elif len(vazias) > 0.5 * n: est = "maioria sem texto (imagem)"
    else: est = "ok"
    def faixa(xs):
        out = []; 
        for x in xs:
            if out and x == out[-1][1] + 1: out[-1][1] = x
            else: out.append([x, x])
        return ",".join(f"{a}" if a == b else f"{a}-{b}" for a, b in out)
    return {"caminho": cam, "texto": est, "paginas_texto": n, "paginas_vazias": faixa(vazias),
            "paginas_problema": faixa(ruins), "chars": len(txt)}

if __name__ == "__main__":
    cat = json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))
    alvo = [(d["caminho"], d["md5"]) for d in cat if d["grupo"] != "SEM_QUESTOES" and not d.get("duplicata_de") or d.get("tipo_duplicata", "").startswith("prov")]
    feitos = set()
    if os.path.exists(SAIDA):
        for l in open(SAIDA, encoding="utf-8"): feitos.add(json.loads(l)["caminho"])
    pend = [a for a in alvo if a[0] not in feitos]
    pend.sort(key=lambda a: 0 if "Provas ENEM" in a[0] or "SSA" in a[0] else 1)
    t0 = time.time(); n = 0
    with Pool(2) as pool, open(SAIDA, "a", encoding="utf-8") as out:
        for r in pool.imap_unordered(proc, pend):
            out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush(); n += 1
            if time.time() - t0 > ORC: pool.terminate(); break
    print(f"alvo {len(alvo)} | feitos antes {len(feitos)} | agora {n} | faltam {len(pend) - n}")
