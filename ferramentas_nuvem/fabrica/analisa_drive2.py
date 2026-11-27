# Fábrica, etapa 1a: baixa cada arquivo do Drive novo pelo ID, mede (md5, páginas, texto por página,
# questões numeradas, respostas de gabarito) e apaga o PDF. Resultado: uma linha JSON por arquivo.
# Uso: python3 -I analisa_drive2.py <lista.json> <saida.jsonl> <pasta_tmp> <pasta_textos> [threads]
# Retomável: pula os IDs que já estão na saída.
import json, os, re, sys, hashlib, gzip, subprocess, threading, time, urllib.request
import concurrent.futures as cf

UA = {"User-Agent": "Mozilla/5.0"}
lista, saida, tmp, txtdir = sys.argv[1:5]
N = int(sys.argv[5]) if len(sys.argv) > 5 else 6
os.makedirs(tmp, exist_ok=True); os.makedirs(txtdir, exist_ok=True)
lock = threading.Lock()

def get(url, alvo, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=300) as r, open(alvo, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b: break
                    f.write(b)
            return
        except Exception:
            if i == tries - 1: raise
            time.sleep(2 ** i)

QPAT = [re.compile(p, re.M | re.I) for p in (
    r"QUEST[ÃA]O\s*[-–:]?\s*(\d{1,3})\b",
    r"^\s*(\d{1,3})\s*[\.\)\-–]\s+\S",
    r"^\s*(\d{1,3})\s{2,}\S",
)]
LET = r"(?:[A-Ea-e]|ANULAD[AO]|[Aa]nulad[ao]|\*|X)"
GPAT = [re.compile(p) for p in (
    r"(?<![\d,\.])(\d{1,3})\s*[\.\)\-–:]?\s*(" + LET + r")(?![A-Za-z0-9])",
)]

def cobertura(nums):
    """faixa [ini, fim] com mais números achados e pelo menos 80% de densidade -> [ini, fim, achados, total_distintos]"""
    s = sorted(set(n for n in nums if 0 < n <= 300)); best = (0, 0, 0)
    for i in range(len(s)):
        for j in range(len(s) - 1, i - 1, -1):
            c = j - i + 1
            if c <= best[2]: break
            if c >= 0.8 * (s[j] - s[i] + 1):
                best = (s[i], s[j], c); break
    return [best[0], best[1], best[2], len(s)]

def mede(item):
    fid = item["id"]; alvo = os.path.join(tmp, fid)
    r = {"gid": fid, "path": item["path"]}
    try:
        get(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t", alvo)
        data = open(alvo, "rb").read()
        r["bytes"] = len(data); r["md5"] = hashlib.md5(data).hexdigest()
        cab = data[:8]
        r["tipo"] = ("pdf" if cab.startswith(b"%PDF") else "html" if data[:200].lower().lstrip().startswith((b"<!doctype html", b"<html"))
                     else "zip" if cab.startswith(b"PK") else "outro")
        del data
        if r["tipo"] == "pdf":
            info = subprocess.run(["pdfinfo", alvo], capture_output=True, text=True, timeout=120).stdout
            m = re.search(r"Pages:\s+(\d+)", info); r["paginas"] = int(m.group(1)) if m else 0
            m = re.search(r"Producer:\s+(.*)", info); r["producer"] = m.group(1)[:60] if m else ""
            m = re.search(r"Creator:\s+(.*)", info); r["creator"] = m.group(1)[:60] if m else ""
            t = subprocess.run(["pdftotext", "-layout", alvo, "-"], capture_output=True, text=True, timeout=600).stdout
            tr = subprocess.run(["pdftotext", alvo, "-"], capture_output=True, text=True, timeout=600).stdout
            pags = t.split("\f")
            r["chars_pag"] = [len(re.sub(r"\s", "", p)) for p in pags[: r["paginas"] or len(pags)]]
            r["cid"] = t.count("(cid:"); r["pua"] = sum(1 for ch in t if 0xE000 <= ord(ch) <= 0xF8FF)
            r["repl"] = t.count("�")
            nq = {}
            for i, p in enumerate(QPAT):
                nq[i] = cobertura(int(x) for x in p.findall(tr))
            r["q_quest"], r["q_num"], r["q_esp"] = nq[0], nq[1], nq[2]
            g = {}
            for m in GPAT[0].finditer(t):
                n = int(m.group(1))
                if 0 < n <= 300: g.setdefault(n, m.group(2))
            r["g_cob"] = cobertura(g.keys())
            # gabarito em tabela: linha de números seguida de linha de letras
            tab = set(); linhas = t.split("\n")
            for a, b in zip(linhas, linhas[1:]):
                na = re.findall(r"\d{1,3}", a); lb = re.findall(r"(?<![A-Za-z])[A-E](?![A-Za-z])", b)
                if len(na) >= 5 and re.fullmatch(r"[\d\s|]+", a.strip()) and len(lb) >= len(na) * 0.8 and re.fullmatch(r"[A-E\s|*X]+", b.strip() or "z"):
                    tab.update(int(x) for x in na)
            r["g_tab"] = cobertura(tab)
            r["trecho"] = re.sub(r"\s+", " ", t[:1500])[:900]
            with gzip.open(os.path.join(txtdir, fid + ".txt.gz"), "wt") as f: f.write(tr)
    except Exception as e:
        r["erro"] = repr(e)[:200]
    finally:
        try: os.remove(alvo)
        except OSError: pass
    return r

itens = json.load(open(lista))
feitos = set()
if os.path.exists(saida):
    for L in open(saida):
        try:
            d = json.loads(L)
            if "erro" not in d: feitos.add(d["gid"])
        except Exception: pass
falta = [i for i in itens if i["id"] not in feitos]
print("total", len(itens), "faltam", len(falta), flush=True)
k = 0
with cf.ThreadPoolExecutor(N) as ex, open(saida, "a") as out:
    for r in ex.map(mede, falta):
        with lock:
            out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush()
        k += 1
        if k % 100 == 0: print(k, "feitos", flush=True)
print("fim", k, flush=True)
