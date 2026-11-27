# Fonte Type1 cuja /Encoding /Differences da o nome do glifo como "/g<GID>" do Arial e cujo ToUnicode nao cobre esse
# codigo: o pdfplumber le "(cid:N)" (ENEM PPL 2010, 2o dia) ou o proprio codigo como letra ("!\"#$%&", ENEM 2011
# regular, 2o dia). Traduz pelo numero do glifo (tabela _banco/cid_unicode.json, indexada pelo GID do Arial; fora dela,
# GID 3-97 = chr(GID+29)). So entram os codigos fora do ToUnicode (os outros o PDF ja traduz certo).
# Grava _banco/cid_unicode/<PID>.json ({"<pagina>|<fonte com prefixo>": {codigo: texto}}), lido pelo 06_extrair.py.
# Uso: cid_difs.py <PID>
import sys,os,json,re
from pypdf import PdfReader
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from catalogo import CAT,R
pid=sys.argv[1]; r=PdfReader(R+"/"+CAT[pid]["caminho"])
T={}
for v in json.load(open(R+"/_banco/cid_unicode.json")).values():
    for k,c in v.items(): T.setdefault(k,c)
def cobertos(f):
    """codigos que o ToUnicode da fonte traduz, e os textos que ele produz"""
    if "/ToUnicode" not in f: return set(),""
    t=f["/ToUnicode"].get_object().get_data().decode("latin1"); s=set(); u=set()
    for bl in re.findall(r"beginbfchar(.*?)endbfchar",t,re.S):
        for a,b in re.findall(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>",bl): s.add(int(a,16)); u.add(chr(int(b[:4],16)))
    for bl in re.findall(r"beginbfrange(.*?)endbfrange",t,re.S):
        for a,b,c in re.findall(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>",bl):
            s|=set(range(int(a,16),int(b,16)+1)); u|={chr(int(c[:4],16)+k) for k in range(int(b,16)-int(a,16)+1)}
    return s,"".join(sorted(u))
out={}; falta=set(); n_=0
for pn,pg in enumerate(r.pages,1):
    fs=pg.get("/Resources",{}).get("/Font",{})
    for f in fs.values():
        f=f.get_object(); enc=f.get("/Encoding")
        # fonte CID do Arial (Identity-H, CID = GID do Arial: ENEM 2014) sem ToUnicode: todos os GIDs conhecidos
        if str(f.get("/Subtype"))=="/Type0" and str(enc)=="/Identity-H" and "Arial" in str(f.get("/BaseFont")):
            d_=f["/DescendantFonts"][0].get_object()
            if str(d_.get("/CIDToGIDMap"))=="/Identity":
                cob,tu=cobertos(f)
                m={str(g):T.get(str(g)) or chr(g+29) for g in set(range(3,98))|{int(k) for k in T if k.isdigit()} if g not in cob}
                m["_tu"]=tu; out["%d|%s"%(pn,str(f.get("/BaseFont"))[1:])]=m; n_+=len(m)-1
            continue
        if not hasattr(enc,"get") or "/Differences" not in enc: continue
        nome=str(f.get("/BaseFont"))[1:]
        if "Arial" not in nome: continue        # a tabela de GID e a do Arial; outra fonte fica como esta (alerta)
        cob,tu=cobertos(f); cod=None; m={}
        for x in enc["/Differences"]:
            if isinstance(x,int) or str(x).isdigit(): cod=int(x); continue
            g=re.fullmatch(r"/g(\d+)",str(x))
            if g and cod not in cob:
                gid=int(g.group(1)); u=T.get(str(gid)) or (chr(gid+29) if 3<=gid<=97 else None)
                if u: m[str(cod)]=u
                else: falta.add((nome,cod,str(x)))
            cod+=1
        # "_tu": letras que o ToUnicode ja produz; uma delas no texto pode ser codigo traduzido certo, nao o codigo cru
        if m: m["_tu"]=tu; out["%d|%s"%(pn,nome)]=m; n_+=len(m)-1
os.makedirs(R+"/_banco/cid_unicode",exist_ok=True)
if out: json.dump(out,open(R+"/_banco/cid_unicode/%s.json"%pid,"w"),ensure_ascii=False,indent=0)
print(pid,"fontes/paginas",len(out),"codigos",n_,"sem traducao:",sorted(falta)[:10])
