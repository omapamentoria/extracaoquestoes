# Gabaritos trocados (prova usou o gabarito da outra prova da mesma pasta): le o gabarito certo pelo nome do arquivo.
import json,glob,sys,re,os,collections
sys.path.insert(0,os.path.dirname(__file__)); from gabh import horizontal
S=sys.argv[1]
cat={x["id"]:x for x in json.load(open("/home/user/extracaoquestoes/_banco/catalogo_debug.json"))}
RX=re.compile(r"(?<![\d,.])(\d{1,3})\s*[-–.:)]?\s+(ANULADA|Anulada|anulada|[A-E])(?![A-Za-zÀ-ÿ\d])")
def vertical(t):
    g={}
    for m in RX.finditer(t): g.setdefault(int(m.group(1)),"anulada" if len(m.group(2))>1 else m.group(2))
    return g
CERTO={}
for p in ["P0793","P0797","P0801","P0805","P0809","P0813","P0816","P0821","P0825"]:
    alvo=re.sub(r"\s*\.pdf$","",cat[p]["arquivo"]).strip()+" GABARITO.pdf"
    CERTO[p]=next(g for g in cat[p]["gabarito_ids"].split() if cat[g]["arquivo"]==alvo)
CERTO.update({"P1334":"P1333","P1337":next(g for g in cat["P1337"]["gabarito_ids"].split() if "2 ED" not in cat[g]["arquivo"]),
              "P1339":next(g for g in cat["P1339"]["gabarito_ids"].split() if "2021.2" in cat[g]["arquivo"]),"P2065":"P2063"})
Q=collections.defaultdict(list)
for f in glob.glob(S+"/partes/*.json"):
    for q in json.load(open(f)):
        o=q.get("origem_texto") or ""; p=o.split("-")[0]
        if p in CERTO and "-Q" in o: Q[p].append((int(o.split("-Q")[1][:3]),o,q))
fix={}; sem=[]
for p,g in CERTO.items():
    t=open(f"{S}/gabs/{g}.txt").read()
    gab=horizontal(t) if p in ("P1334","P1337","P1339") else vertical(t)
    if p in ("P1334","P1337","P1339"):   # linguas 16-20 aparecem duas vezes: nao usa
        nums=[int(x) for x in re.findall(r"\b\d{1,3}\b"," ".join(l for l in t.split("\n") if not re.search(r"[A-Za-z]{2,}",l)))]
        dup={n for n in nums if nums.count(n)>1}
        gab={k:v for k,v in gab.items() if k not in dup}
    mud=0
    for n,o,q in Q[p]:
        if n not in gab or "-ING" in o or "-ESP" in o: sem.append(q["id"]); continue
        novo=gab[n].lower() if gab[n].lower()=="anulada" else gab[n]
        if novo!=q["gabarito"]: fix[q["id"]]=(q["gabarito"],novo,p,n); mud+=1
    print(p,cat[p]["arquivo"],"->",cat[g]["arquivo"],"questoes",len(Q[p]),"mudam",mud)
print("total mudam",len(fix),"sem gabarito lido",len(sem),sem)
json.dump({"fix":{str(k):v for k,v in fix.items()},"sem":sem},open(S+"/fix_gab_trocado.json","w"))
