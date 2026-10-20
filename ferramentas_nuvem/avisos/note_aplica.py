import json,glob,sys,re
S=sys.argv[1]; N=json.load(open(S+"/note_adote.json"))
Q={}
for f in glob.glob(S+"/partes/*.json"):
    for q in json.load(open(f)): Q[q["id"]]=q
norm=lambda s:re.sub(r"\s+","",re.sub(r"</?su[bp]>","",s))
fix={};pend=[]
for i,v in N.items():
    q=Q[int(i)]; al=v["alts"]; ok=True; nota=[]; novas=[]
    if len(al)!=len(q["alternativas"]): pend.append((i,"nº alts")); continue
    for a in q["alternativas"]:
        t=a["texto"]; pa=al.get(a["letra"],"")
        # acha o ponto de corte em t cujo prefixo normalizado = pa normalizado
        alvo=norm(pa); cut=None
        for k in range(1,len(t)+1):
            if norm(t[:k])==alvo and (k==len(t) or t[k]==" "): cut=k; break
        if cut is None or not alvo: ok=False; break
        novas.append(t[:cut].strip()); r=t[cut:].strip()
        if r: nota.append(r)
    if not ok: pend.append((i,"alternativa não bate com o PDF")); continue
    nt=" ".join(nota)
    if not re.match(r"Note e [Aa]dote",nt): pend.append((i,"nota não começa em Note e adote: "+nt[:60])); continue
    fix[int(i)]={"alts":novas,"nota":nt}
    print(i,novas,"|",nt)
print("PENDENTES",pend)
json.dump(fix,open(S+"/fix_note.json","w"),ensure_ascii=False,indent=1)
