# Questoes 1-5 de ingles/espanhol: o gabarito da propria prova tem dois blocos com o mesmo numero; escolhe pelo conteudo
# e so aceita se a explicacao (V) bater com o texto da alternativa da mesma letra.
import json,sys,re
S=sys.argv[1]; cat={x["id"]:x for x in json.load(open("/home/user/extracaoquestoes/_banco/catalogo_debug.json"))}
Q=json.load(open(S+"/quar_in.json")); SG=json.load(open(S+"/sas_gab.json"))
W=lambda s:{w for w in re.findall(r"[a-zà-úñ]{4,}",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower()))}
res={}
for q in Q:
    o=q.get("origem_texto") or ""
    if not ("-ING" in o or "-ESP" in o): continue
    p=o.split("-")[0]; n=int(o.split("-Q")[1][:3]); g=SG.get(p,{}).get("gab") or (cat[p]["gabarito_ids"] or "").split()[0]
    try: bl=[b for b in json.load(open(f"{S}/blocos/{g}.json")) if b["n"]==n]
    except FileNotFoundError: continue
    wq=W(q["statement"]+" "+" ".join(a["texto"] for a in q["alternativas"]))
    cands=sorted(bl,key=lambda b:-len(wq&W(b["txt"])))
    if not cands: continue
    b=cands[0]; s1=len(wq&W(b["txt"])); s2=len(wq&W(cands[1]["txt"])) if len(cands)>1 else 0
    vs=re.findall(r"\b([a-e])\)\s*\(V\)(.{0,400}?)(?=\b[a-e]\)\s*\([VF]\)|$)",b["txt"],re.S)
    ok=s1>=4 and s1>=2*max(1,s2)
    if vs:
        L,t=vs[0]; wt=W(t); alts={a["letra"]:W(a["texto"]) for a in q["alternativas"]}
        m=max(alts,key=lambda k:len(alts[k]&wt))
        ok=ok and L.upper()==b["resp"] and (m==L.upper() or not alts[m]&wt)
    res[q["id"]]={"resp":b["resp"],"ok":ok,"s1":s1,"s2":s2,"atual":q["gabarito"]}
json.dump(res,open(S+"/lingua.json","w")); print("aceitas",sum(v["ok"] for v in res.values()),"de",len(res))
