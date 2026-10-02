# Monta _banco/cid_unicode.json: para cada fonte (nome sem o prefixo do subconjunto e sem "-Identity-H"), o caractere
# de cada numero de glifo, tirado da tabela ToUnicode de PDFs que tem essa tabela. Serve para traduzir o "(cid:N)" de
# PDFs com a MESMA fonte sem ToUnicode (ENEM 2017-2018: Arial CFF sem tabela). Conflito entre PDFs = glifo descartado.
# Uso: python3 ferramentas_nuvem/tabela_cid.py PID...   (baixa os PDFs do Drive se faltarem)
import json, os, re, sys, glob, collections
from io import BytesIO
import pdfplumber
from pdfminer.pdftypes import resolve1
from pdfminer.cmapdb import CMapParser, FileUnicodeMap
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(R, "_banco"); BM = os.path.expanduser("~/mnt/BM")
CAT = {r["id"]: r for r in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
OUT = os.path.join(B, "cid_unicode.json")
tab = json.load(open(OUT)) if os.path.exists(OUT) else {}
votos = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
for b, t in tab.items():
    for c, u in t.items(): votos[b][c][u] += 100
def base(n): return re.sub(r"-Identity-[HV]$", "", re.sub(r"^[A-Z]{6}\+", "", n))
mapa = json.load(open(os.path.join(R, "ferramentas_nuvem", "mapa_drive.json")))
falta = [x for x in mapa if x["pid"] in sys.argv[1:] and not os.path.exists(os.path.join(BM, x["path"]))]
if falta:
    json.dump(falta, open("/tmp/tab_cid.json", "w")); os.system(f"{sys.executable} {R}/ferramentas_nuvem/drive_sync.py baixar /tmp/tab_cid.json {BM} >/dev/null")
for pid in sys.argv[1:]:
    pdf = pdfplumber.open(os.path.join(BM, CAT[pid]["caminho"])); vistos = set()
    for pg in pdf.pages:
        fonts = resolve1(resolve1(pg.page_obj.resources).get("Font", {})) or {}
        for f in fonts.values():
            f = resolve1(f)
            if "ToUnicode" not in f or f.get("Subtype") is None or f["Subtype"].name != "Type0": continue
            ref = f["ToUnicode"]
            if id(ref) in vistos: continue
            vistos.add(id(ref))
            cm = FileUnicodeMap()
            try: CMapParser(cm, BytesIO(resolve1(ref).get_data())).run()
            except Exception: continue
            # so fonte com a numeracao ORIGINAL dos glifos (subconjunto renumerado nao serve para outro PDF): na ordem
            # original, os caracteres ASCII ficam em (codigo - 29) ("a" = 68, espaco = 3)
            asc = [(cid, u) for cid, u in cm.cid2unichr.items() if u and len(u) == 1 and 32 <= ord(u) < 127]
            if len(asc) < 10 or any(cid != ord(u) - 29 for cid, u in asc): continue
            for cid, u in cm.cid2unichr.items():
                if u and u != "�": votos[base(f["BaseFont"].name)][str(cid)][u] += 1
    print(pid, "ok")
out = {}
for b, t in votos.items():
    # divergencia entre PDFs: vale a leitura de pelo menos 80% dos votos
    out[b] = {c: us.most_common(1)[0][0] for c, us in t.items() if us.most_common(1)[0][1] >= 0.8 * sum(us.values())}
    if b.startswith("Arial"): out[b].update({"191": "fi", "192": "fl"})   # ligaduras da Arial (ordem original dos glifos)
    conf = [c for c in t if c not in out[b]]
    print(b, len(out[b]), "glifos", f"({len(conf)} em conflito, descartados)" if conf else "")
json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=0, sort_keys=True)
