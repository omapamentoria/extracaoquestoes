# Auditoria de gabarito do banco: baixa do Drive cada gabarito ligado a cada prova e mede a concordancia com o banco.
import json,glob,sys,collections,os,re,subprocess
S=sys.argv[1]; D=S+"/gabs"; os.makedirs(D,exist_ok=True)
X="/home/user/extracaoquestoes"
cat={x["id"]:x for x in json.load(open(X+"/_banco/catalogo_debug.json"))}
drv={m["pid"]:m["id"] for m in json.load(open(X+"/ferramentas_nuvem/mapa_drive.json"))}
prov=collections.defaultdict(dict)
for f in glob.glob(S+"/partes/*.json"):
    for q in json.load(open(f)):
        u=q.get("origem_texto") or ""; p=u.split("-")[0]
        if p in cat and "-Q" in u:
            prov[p][int(u.split("-Q")[1][:3])]=(q["id"],q["gabarito"])
def texto(g):
    t=f"{D}/{g}.txt"
    if not os.path.exists(t):
        if g not in drv: return None
        subprocess.run(["curl","-sSL","-o",f"{D}/{g}.pdf",f"https://drive.usercontent.google.com/download?id={drv[g]}&export=download&confirm=t"])
        subprocess.run(["pdftotext","-layout",f"{D}/{g}.pdf",t]); 
        try: os.remove(f"{D}/{g}.pdf")
        except: pass
    return open(t,errors="ignore").read() if os.path.exists(t) else None
RX=re.compile(r"(?<![\d,.])(\d{1,3})\s*[-–.:)]?\s+(ANULADA|Anulada|anulada|[A-E])(?![A-Za-zÀ-ÿ])")
res=[]
for p,qs in sorted(prov.items()):
    c=cat[p]; ids=(c.get("gabarito_ids") or "").split() or (c.get("resolucao_ids") or "").split()
    linha={"pid":p,"arquivo":c["arquivo"],"conjunto":c.get("conjunto"),"n":len(qs),"chaves":[]}
    for g in ids:
        t=texto(g)
        if t is None: linha["chaves"].append({"g":g,"erro":"sem texto"}); continue
        par={}
        for m in RX.finditer(t):
            n=int(m.group(1)); par.setdefault(n,m.group(2)[0].upper() if m.group(2)[0] in "Aa" and len(m.group(2))>1 else m.group(2))
        comp=[(n,b,par[n]) for n,(i,b) in qs.items() if n in par]
        ok=sum(1 for n,b,o in comp if b==o or (o=="A" and False))
        linha["chaves"].append({"g":g,"arq":cat.get(g,{}).get("arquivo"),"cobre":len(comp),"ok":ok,
            "difs":[(n,qs[n][0],b,o) for n,b,o in comp if b!=o]})
    res.append(linha); print(p,c["arquivo"],[(k.get("arq"),k.get("ok"),k.get("cobre")) for k in linha["chaves"]],flush=True)
json.dump(res,open(S+"/auditoria_gab.json","w"),ensure_ascii=False,indent=0)
