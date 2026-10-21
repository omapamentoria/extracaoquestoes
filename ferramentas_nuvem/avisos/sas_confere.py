# Confere se cada bloco da resolucao fala da mesma questao do banco (palavras de conteudo em comum).
import json,glob,sys,re,collections
S=sys.argv[1]; G=json.load(open(S+"/sas_gab.json"))
STOP=set("a o e de da do das dos em no na nos nas um uma que para com por se ao as os é não mais como ser pelo pela pode foi está entre sua seu suas seus isso esse essa este esta são ou já também quando sobre ele ela qual".split())
W=lambda s:{w for w in re.findall(r"[a-zà-ú]{5,}",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower())) if w not in STOP}
out={}; 
for f in glob.glob(S+"/partes/*.json"):
    for q in json.load(open(f)):
        o=q.get("origem_texto") or ""; p=o.split("-")[0]
        if p not in G or "-Q" not in o: continue
        n=str(int(o.split("-Q")[1][:3])); b=G[p]["blocos"].get(n)
        if b is None: out[q["id"]]=(p,None,None,q["gabarito"]); continue
        wq=W(q["statement"]+" "+" ".join(a["texto"] for a in q["alternativas"])); wb=W(b)
        sc=len(wq&wb)/max(1,min(len(wq),len(wb)))
        out[q["id"]]=(p,round(sc,2),G[p]["gabarito"][n],q["gabarito"])
por=collections.defaultdict(list)
for i,(p,sc,g,b) in out.items(): por[p].append(sc)
for p in sorted(por):
    v=[x for x in por[p] if x is not None]
    print(p,len(por[p]),"sem bloco",por[p].count(None),"media",round(sum(v)/max(1,len(v)),2),"baixos(<0.12)",sum(1 for x in v if x<0.12))
json.dump(out,open(S+"/sas_confere.json","w"))
