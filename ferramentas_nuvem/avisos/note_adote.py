# FUVEST: separa o "Note e adote" (caixa ao lado das alternativas) do texto das alternativas, lendo o layout do PDF.
import json,glob,sys,re,os,subprocess
S=sys.argv[1]; P=S+"/pdf"
drv={m["pid"]:m["id"] for m in json.load(open("/home/user/extracaoquestoes/ferramentas_nuvem/mapa_drive.json"))}
Q={}
for f in glob.glob(S+"/partes/*.json"):
    for q in json.load(open(f)): Q[q["id"]]=q
alvo=[q for q in Q.values() if any(re.search(r"Note e [Aa]dote",a["texto"]) for a in q["alternativas"])]
out={}
for q in sorted(alvo,key=lambda q:q["id"]):
    pid=q["origem_texto"].split("-")[0]
    if not os.path.exists(f"{P}/{pid}.txt"):
        subprocess.run(["curl","-sSL","-o",f"{P}/{pid}.pdf",f"https://drive.usercontent.google.com/download?id={drv[pid]}&export=download&confirm=t"])
        subprocess.run(["pdftotext","-layout",f"{P}/{pid}.pdf",f"{P}/{pid}.txt"],stderr=subprocess.DEVNULL)
    L=open(f"{P}/{pid}.txt").read().split("\n")
    alts=q["alternativas"]; a0=alts[0]["texto"].split()[0]
    cand=[i for i,l in enumerate(L) if re.search(r"\(A\)\s+"+re.escape(a0),l)]
    # perto de "Note e adote"
    cand=[i for i in cand if any(re.search(r"Note e [Aa]dote",L[j]) for j in range(max(0,i-3),i+3))]
    if len(cand)!=1: print(q["id"],"?? candidatos",cand); continue
    i=cand[0]; c0=L[i].index("(A)")
    j=next(j for j in range(i-3,i+3) if re.search(r"Note e [Aa]dote",L[j])); x=re.search(r"Note e [Aa]dote",L[j]).start()
    esq,dir_=[],[]; k=i; vistoE=False
    # linhas de nota acima do (A)
    for jj in range(j,i): dir_.append(L[jj][x:].strip())
    while k<len(L):
        l=L[k]; e=l[c0:x].strip() if len(l)>c0 else ""; d=l[x:].strip() if len(l)>x else ""
        if vistoE and (not e and not d): break
        if vistoE and e.startswith("(") is False and re.match(r"^\d{1,2}\s*$",e): break
        if re.match(r"\(E\)",e): vistoE=True
        if e: esq.append(e)
        if d: dir_.append(d)
        k+=1
        if vistoE and not d and k<len(L) and not L[k][c0:x].strip(): break
    txt=" ".join(esq); partes=re.split(r"\(([A-E])\)\s*",txt)[1:]
    novas=dict(zip(partes[0::2],[p.strip() for p in partes[1::2]]))
    nota=" ".join(d for d in dir_ if d)
    out[q["id"]]={"alts":novas,"nota":nota}
    print(q["id"],pid,novas,"| NOTA:",nota[:200])
json.dump(out,open(S+"/note_adote.json","w"),ensure_ascii=False,indent=1)
