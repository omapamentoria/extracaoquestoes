# Gabarito comentado que repete a questao inteira: le por coluna (layout), bloco "QUESTAO N" ... "Resposta correta/Gabarito: X";
# aceita so se o bloco da propria prova, mesmo numero, repete >=60% das palavras da questao e a resposta e unica.
import json,sys,re,collections,subprocess,os
S=sys.argv[1]; cat={x["id"]:x for x in json.load(open("/home/user/extracaoquestoes/_banco/catalogo_debug.json"))}
STOP=set("a o e de da do das dos em no na nos nas um uma que para com por se ao as os é não mais como".split())
W=lambda s:{w for w in re.findall(r"[a-zà-ú]{5,}",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower())) if w not in STOP}
R=re.compile(r"(?:Resposta correta|Gabarito)\s*:\s*([A-E])\b")
def cols(g):
    t=subprocess.run(["pdftotext","-layout",f"{S}/gabs/{g}.pdf","-"],capture_output=True,text=True).stdout; out=[]
    for pg in t.split("\f"):
        L=pg.split("\n"); pos=[m.start() for l in L for m in re.finditer(r"(?i)QUEST[ÃA]O|Resposta correta|Gabarito:",l) if m.start()>30]
        c=collections.Counter(pos).most_common(1)[0][0] if pos else 10**6
        out.append("\n".join(l[:c] for l in L)); out.append("\n".join(l[c:] for l in L))
    return "\n".join(out)
ok=json.load(open(S+"/quar_resolvidas.json")); novos={}; cache={}
for q in json.load(open(S+"/quar_in.json")):
    o=q.get("origem_texto") or ""; p=o.split("-")[0]
    if str(q["id"]) in ok or p not in cat or "-Q" not in o: continue
    n=int(o.split("-Q")[1][:3]); lang="ING" if "-ING" in o else "ESP" if "-ESP" in o else None
    wq=W(q["statement"]+" "+" ".join(a["texto"] for a in q["alternativas"]))
    for g in (cat[p]["gabarito_ids"] or "").split():
        if not os.path.exists(f"{S}/gabs/{g}.pdf"): continue
        if g not in cache:
            t=cols(g); hs=list(re.finditer(r"(?i)QUEST[ÃA]O\s+(\d{1,3})",t)); bl=collections.defaultdict(list)
            for i,h in enumerate(hs):
                b=t[h.end():hs[i+1].start() if i+1<len(hs) else len(t)]; r=set(R.findall(b))
                if len(r)==1: bl[int(h.group(1))].append((r.pop(),b))
            cache[g]=bl
        boas={r for r,b in cache[g].get(n,[]) if len(wq&W(b))/max(1,len(wq))>=0.6}
        if len(boas)==1: novos[str(q["id"])]=boas.pop(); break
print("novas",len(novos),collections.Counter(k for k in (json.load(open(S+"/quar_in.json")) and [])))
ok.update(novos); json.dump(ok,open(S+"/quar_resolvidas.json","w")); print("total",len(ok))
