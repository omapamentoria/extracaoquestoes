# Localizador por conteudo: para cada questao, procura em TODOS os gabaritos/resolucoes da mesma marca o bloco que fala
# dela (palavras raras em comum) e le a resposta oficial do bloco. So aceita se o melhor bloco for claramente o unico.
# Uso: localiza.py <av> <ids.json> <saida.json> [--teste]
import json,sys,re,os,subprocess,collections,math,glob
S,IDS,OUT=sys.argv[1:4]
X="/home/user/extracaoquestoes"
cat={x["id"]:x for x in json.load(open(X+"/_banco/catalogo_debug.json"))}
drv={m["pid"]:m["id"] for m in json.load(open(X+"/ferramentas_nuvem/mapa_drive.json"))}
alvo=json.load(open(IDS))   # lista de questoes completas
STOP=set("a o e de da do das dos em no na nos nas um uma que para com por se ao as os é não mais como ser pelo pela pode foi está entre sua seu suas seus isso esse essa este esta são ou já também quando sobre ele ela qual alternativa correta resposta questão texto".split())
W=lambda s:[w for w in re.findall(r"[a-zà-ú]{4,}|\d+[,.]?\d*",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower())) if w not in STOP]
def colunas(pdf):
    try:
        import pdfplumber
        out=[]
        with pdfplumber.open(pdf) as P:
            for pg in P.pages:
                w=pg.width
                for x0,x1 in ((0,w/2),(w/2,w)): out.append(pg.crop((x0,0,x1,pg.height)).extract_text() or "")
        return "\n".join(out)
    except Exception: return ""
RESP=re.compile(r"(?:Resposta\s+correta|ITEM\s+CORRETO|Gabarito|Alternativa\s+correta|Alternativa)\s*[:\-–]?\s*(?:letra\s+)?\(?([A-E])\)?(?![\wÀ-ÿ])")
HEAD=re.compile(r"^\s*(?:QUEST[ÃA]O\s+)?(\d{1,3})\s*[.:)\-–]\s|^\s*QUEST[ÃA]O\s+(\d{1,3})\b",re.M|re.I)
def blocos(g):
    cache=f"{S}/blocos/{g}.json"
    if os.path.exists(cache): return json.load(open(cache))
    os.makedirs(f"{S}/blocos",exist_ok=True); pdf=f"{S}/gabs/{g}.pdf"
    if not os.path.exists(pdf) and g in drv: subprocess.run(["curl","-sSL","-o",pdf,f"https://drive.usercontent.google.com/download?id={drv[g]}&export=download&confirm=t"])
    t=colunas(pdf) if os.path.exists(pdf) else ""
    hs=list(HEAD.finditer(t)); bl=[]
    for i,h in enumerate(hs):
        b=t[h.end():hs[i+1].start() if i+1<len(hs) else len(t)]
        r=set(RESP.findall(b))
        if len(r)==1: bl.append({"n":int(h.group(1) or h.group(2)),"resp":r.pop(),"txt":b[:2500]})
    json.dump(bl,open(cache,"w")); return bl
def raiz(p): return "/".join(cat[p]["caminho"].split("/")[:-3 if "Simulados SAS" in cat[p]["caminho"] or "censured" in cat[p]["caminho"] else -2])
res={}
pools={}
for q in alvo:
    p=(q.get("origem_texto") or "").split("-")[0]
    if p not in cat: continue
    r=raiz(p)
    if r not in pools:
        ks=[g for g,x in cat.items() if x["caminho"].startswith(r+"/") and x.get("papel") in ("gabarito","resolucao")]
        B=[]
        for g in ks:
            for b in blocos(g): B.append({**b,"g":g})
        df=collections.Counter(w for b in B for w in set(W(b["txt"])))
        pools[r]=(B,df,len(B)); print("pasta",r[-60:],"chaves",len(ks),"blocos",len(B),flush=True)
    B,df,N=pools[r]
    wq=set(W(q["statement"]+" "+" ".join(a["texto"] for a in q["alternativas"])))
    sc=[]
    for b in B:
        com=wq&set(W(b["txt"]))
        sc.append((sum(math.log(N/(1+df[w])) for w in com),len(com),b))
    sc.sort(key=lambda x:-x[0])
    if not sc: continue
    s1,n1,b1=sc[0]; s2=next((s for s,n,b in sc[1:] if b["resp"]!=b1["resp"] or b["g"]!=b1["g"] or b["n"]!=b1["n"]),0)
    num=int(q["origem_texto"].split("-Q")[1][:3]) if "-Q" in (q.get("origem_texto") or "") else None
    ok= n1>=8 and s1>=1.6*s2 and b1["n"]==num
    # resolucao que comenta cada alternativa: a explicacao (V) tem que casar com o texto da alternativa da mesma letra
    vs=re.findall(r"([a-e])\)\s*\(V\)(.{0,400}?)(?=[a-e]\)\s*\([VF]\)|$)",b1["txt"],re.S)
    if ok and vs:
        L,txt=vs[0]; wt=set(W(txt))
        alts={a["letra"]:set(W(a["texto"])) for a in q["alternativas"]}
        melhor=max(alts,key=lambda k:len(alts[k]&wt))
        if L.upper()!=b1["resp"] or (alts[melhor]&wt and melhor!=L.upper()): ok=False
    res[q["id"]]={"resp":b1["resp"],"ok":ok,"s1":round(s1,1),"s2":round(s2,1),"n":n1,"g":b1["g"],"num":b1["n"],"atual":q["gabarito"]}
json.dump(res,open(OUT,"w"),indent=0)
print("aceitas",sum(v["ok"] for v in res.values()),"de",len(res))
