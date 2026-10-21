# SAS: aceita o gabarito do bloco de mesmo numero da propria resolucao quando a explicacao "(V)" casa claramente com o texto
# da alternativa da mesma letra (e com nenhuma outra). Modo --teste mede nas questoes ja confirmadas.
import json,sys,re,glob
S=sys.argv[1]; TESTE="--teste" in sys.argv; SG=json.load(open(S+"/sas_gab.json"))
W=lambda s:{w for w in re.findall(r"[a-zà-ú]{4,}|\d+",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower()))}
def decide(q):
    o=q.get("origem_texto") or ""; p=o.split("-")[0]
    if p not in SG or "-Q" not in o or "-ING" in o or "-ESP" in o: return None
    n=int(o.split("-Q")[1][:3]); g=SG[p]["gab"]
    try: bl=[b for b in json.load(open(f"{S}/blocos/{g}.json")) if b["n"]==n]
    except FileNotFoundError: return None
    if len(bl)!=1: return None
    b=bl[0]; vs=re.findall(r"\b([a-e])\)\s*\(V\)(.{0,500}?)(?=\b[a-e]\)\s*\([VF]\)|$)",b["txt"],re.S)
    if len(vs)!=1 or vs[0][0].upper()!=b["resp"]: return None
    wt=W(vs[0][1]); sc=sorted(((len(W(a["texto"])&wt)/max(1,len(W(a["texto"]))),a["letra"]) for a in q["alternativas"]),reverse=True)
    if sc[0][1]==b["resp"] and sc[0][0]>=0.5 and sc[0][0]>=sc[1][0]+0.25: return b["resp"]
    return None
if TESTE:
    L=json.load(open(S+"/log_aplica.json")); ids={int(i) for i,k,m in L if k=="gabarito" and "SAS" in m}
    Q=[q for f in glob.glob("/home/user/bq-avisos/final/partes/*.json") for q in json.load(open(f)) if q["id"] in ids]
    r=[(decide(q),q["gabarito"]) for q in Q]; a=[x for x in r if x[0]]
    print("teste: aceitas",len(a),"de",len(r),"acertos",sum(x==y for x,y in a))
else:
    ok=json.load(open(S+"/quar_resolvidas.json")); nov={}
    for q in json.load(open(S+"/quar_in.json")):
        if str(q["id"]) in ok: continue
        d=decide(q)
        if d: nov[str(q["id"])]=d
    print("novas",len(nov)); ok.update(nov); json.dump(ok,open(S+"/quar_resolvidas.json","w")); print("total",len(ok))
