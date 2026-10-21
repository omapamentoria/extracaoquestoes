# Banco MAPA - passo 4: acha PDFs com o mesmo conteudo (copias, outra cor/tipo de caderno, versao "com gabarito").
# Usa o texto extraido (passo 3). Assinatura bottom-k de trechos de 6 palavras. Saida: _banco/similares.jsonl
import os, json, gzip, re, hashlib, collections, sys
RAIZ = os.path.expanduser("~/mnt/BM"); B = os.path.join(RAIZ, "_banco"); TX = os.path.join(B, "texto")
K = 128
cat = json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))
leg = {json.loads(l)["caminho"] for l in open(os.path.join(B, "legibilidade.jsonl"), encoding="utf-8")}
sig = {}; voc = {}; tam = {}; CAM = {d["id"]: d["caminho"] for d in cat}
for d in cat:
    if d["caminho"] not in leg: continue
    p = os.path.join(TX, d["md5"] + ".txt.gz")
    if not os.path.exists(p): continue
    w = re.findall(r"\w+", gzip.open(p, "rt", encoding="utf-8").read().lower())
    if len(w) < 300: continue
    hs = set()
    for i in range(0, len(w) - 5):
        hs.add(int.from_bytes(hashlib.blake2b(" ".join(w[i:i+6]).encode(), digest_size=8).digest(), "big"))
    sig[d["id"]] = sorted(hs)[:K]; tam[d["id"]] = len(hs)
    vs = {int.from_bytes(hashlib.blake2b(x.encode(), digest_size=8).digest(), "big") for x in set(w) if len(x) >= 4 and not x.isdigit()}
    voc[d["id"]] = sorted(vs)[:256]
inv = collections.defaultdict(list)
for i, s in sig.items():
    for h in s: inv[h].append(i)
for i, s in voc.items():
    for h in s[:64]: inv[("v", h)].append(i)
par = collections.Counter()
for h, ids in inv.items():
    if len(ids) > 80: continue
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            par[tuple(sorted((ids[a], ids[b])))] += 1
out = open(os.path.join(B, "similares.jsonl"), "w", encoding="utf-8"); n = 0
for (a, b), c in par.items():
    if c < 12: continue
    def jac(x, y, k):
        sa, sb = set(x), set(y); uni = sorted(sa | sb)[:k]
        return sum(1 for h in uni if h in sa and h in sb) / len(uni)
    j = jac(sig[a], sig[b], K); jv = jac(voc[a], voc[b], 256)
    if j >= 0.3 or jv >= 0.6:
        out.write(json.dumps({"a": CAM[a], "b": CAM[b], "jaccard": round(j, 3), "vocab": round(jv, 3), "shingles_a": tam[a], "shingles_b": tam[b]}) + "\n"); n += 1
print("assinaturas:", len(sig), "| pares similares (>=0.3):", n)
