# Realinha alternativas deslocadas (texto da alternativa escorregou para a seguinte) usando o inicio de cada alternativa no PDF.
import json,glob,sys,re
S=sys.argv[1]; pids=sys.argv[2:]
Q=[q for f in glob.glob(S+"/partes/*.json") for q in json.load(open(f)) if (q.get("origem_texto") or "").split("-")[0] in pids]
N=lambda s:re.sub(r"[^0-9A-Za-zÀ-ÿ]","",re.sub(r"</?su[bp]>|\*","",s))
starts={}
for p in pids:
    for l in open(f"{S}/pdf/{p}.txt"):
        for m in re.finditer(r"(?:^|\s{2,})([A-E])\s{3,}(\S(?:(?!\s{3}).){9,})",l.rstrip()):
            starts.setdefault(p,[]).append((m.group(1),N(m.group(2))[:40]))
fix={}; nada=0; falha=[]
for q in Q:
    p=q["origem_texto"].split("-")[0]; alts=q["alternativas"]
    if len(alts)!=5 or any("{{" in a["texto"] for a in alts): continue
    paras=q["statement"].rstrip().split("\n\n"); 
    # texto conjunto: ultimos paragrafos do enunciado + alternativas
    tail=paras[-1]; conc=tail+" "+" ".join(a["texto"] for a in alts)
    Nc=N(conc); pos=[]; ok=True
    for L in "ABCDE":
        cands=sorted({Nc.find(s,(pos[-1]+1) if pos else 0) for l,s in starts[p] if l==L and len(s)>=8}-{-1})
        if not cands: ok=False; break
        pos.append(cands[0])
    if not ok: falha.append(q["id"]); continue
    # mapeia posicoes normalizadas de volta ao texto original
    idx=[i for i,ch in enumerate(conc) if N(ch)]
    cut=[idx[x] for x in pos]
    novas=[conc[cut[k]:(cut[k+1] if k<4 else len(conc))].strip() for k in range(5)]
    resto=conc[:cut[0]].strip()
    if [a["texto"].strip() for a in alts]==novas: nada+=1; continue
    if min(len(x) for x in novas)<4 or any(re.search(r"(.{25,}).*\1",x) for x in novas) or any(not re.search(r"[.!?)%\dA-Za-zà-ú>]$",x) for x in novas): falha.append(q["id"]); continue
    novo_enun="\n\n".join(paras[:-1]+([resto] if resto else []))
    fix[q["id"]]={"statement":novo_enun,"alts":novas,"antes":[a["texto"] for a in alts]}
print("corrigir",len(fix),"ja certas",nada,"falha",len(falha),falha[:20])
json.dump(fix,open(S+"/fix_realinha.json","w"),ensure_ascii=False,indent=1)
for i in list(fix)[:4]: print(i,fix[i]["statement"][-80:],"||",fix[i]["alts"])
