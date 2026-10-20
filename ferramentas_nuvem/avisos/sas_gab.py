# Le o gabarito das resolucoes SAS ("NN. C1 H1 ... Resposta correta: X"), coluna por coluna.
import json,sys,re,os,subprocess,pdfplumber,collections
S=sys.argv[1]; pids=sys.argv[2:]
cat={x["id"]:x for x in json.load(open("/home/user/extracaoquestoes/_banco/catalogo_debug.json"))}
drv={m["pid"]:m["id"] for m in json.load(open("/home/user/extracaoquestoes/ferramentas_nuvem/mapa_drive.json"))}
def texto_colunas(pdf):
    out=[]
    with pdfplumber.open(pdf) as P:
        for pg in P.pages:
            w=pg.width
            for x0,x1 in ((0,w/2),(w/2,w)):
                out.append(pg.crop((x0,0,x1,pg.height)).extract_text() or "")
    return "\n".join(out)
import os.path
res=json.load(open(S+"/sas_gab.json")) if os.path.exists(S+"/sas_gab.json") else {}
for p in pids:
    p,_,gg=p.partition("=")
    for g in (gg or cat[p]["gabarito_ids"] or "").split():
        f=f"{S}/gabs/{g}.pdf"
        if not os.path.exists(f): subprocess.run(["curl","-sSL","-o",f,f"https://drive.usercontent.google.com/download?id={drv[g]}&export=download&confirm=t"])
        t=texto_colunas(f)
        hs=list(re.finditer(r"(?m)^\s*(\d{1,3})\.\s*C\s?\d+\s*H\s?\d+",t))
        if len(hs)<10:   # formato antigo: "N. texto ... Resposta correta: X" (a resposta pertence ao ultimo "N." antes dela)
            hs=[]; last=0
            for m in re.finditer(r"(?m)^\s*(\d{1,3})\.\s|Resposta\s+correta:",t):
                if m.group(1) and (not hs or int(m.group(1))>=int(hs[-1].group(1)) or int(m.group(1))==1): hs.append(m)
        gab={}; blocos={}; dup={int(h.group(1)) for h in hs if [x.group(1) for x in hs].count(h.group(1))>1}
        for i,h in enumerate(hs):
            blk=t[h.end():hs[i+1].start() if i+1<len(hs) else len(t)]
            r=set(re.findall(r"Resposta\s+correta:\s*([A-E])\b",blk)); v=set(x.upper() for x in re.findall(r"\b([a-e])\)\s*\(V\)",blk))
            an=re.search(r"(?i)anulad",blk)
            if int(h.group(1)) in dup: continue
            if len(r)==1 and (not v or v==r): gab[int(h.group(1))]=r.pop(); blocos[int(h.group(1))]=blk[:1500]
        res[p]={"gab":g,"lidas":len(hs),"gabarito":gab,"blocos":blocos}
        print(p,g,"cabecalhos",len(hs),"lidas",len(gab),flush=True)
json.dump(res,open(S+"/sas_gab.json","w"),indent=0)
