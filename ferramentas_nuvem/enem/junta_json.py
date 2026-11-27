# Junta varios ramos do banco questao por questao (merge de 3 vias por id), para partes em que o git acusa conflito
# porque o arquivo e uma linha so. Para cada id: se so um ramo mudou, vale a mudanca; se dois mudaram de jeitos
# diferentes, e conflito de verdade (para e lista).
# Uso: junta_json.py <repo> <base_ref> <ramo>... -> grava as partes juntas no checkout atual
import json,subprocess,sys,collections
repo,base,ramos=sys.argv[1],sys.argv[2],sys.argv[3:]
def ls(ref): return [l.split("\t")[1] for l in subprocess.run(["git","-C",repo,"ls-tree","-r",ref,"final/partes/"],capture_output=True,text=True).stdout.splitlines()]
def ler(ref,p):
    r=subprocess.run(["git","-C",repo,"show",f"{ref}:{p}"],capture_output=True,text=True)
    return (json.loads(r.stdout),r.stdout.count("\n")<=1) if r.returncode==0 else (None,None)
arqs=sorted(set(ls(base)).union(*[ls(r) for r in ramos]))
conflitos=[];tot=collections.Counter()
for p in arqs:
    B,compacto=ler(base,p); bd={q["id"]:q for q in (B or [])}; ordem=[q["id"] for q in (B or [])]
    res=dict(bd); dono={}
    for r in ramos:
        R,c=ler(r,p)
        if R is None: continue
        if compacto is None: compacto=c
        rd={q["id"]:q for q in R}
        for i,q in rd.items():
            if bd.get(i)==q: continue
            if i in dono and res[i]!=q: conflitos.append((p,i,dono[i],r)); continue
            res[i]=q; dono[i]=r
            if i not in ordem: ordem.append(i)
            tot[r]+=1
        for i in bd:
            if i not in rd:
                if i in dono and dono[i]!=r: conflitos.append((p,i,dono[i],r+" (apagou)")); continue
                res.pop(i,None); dono[i]=r; tot[r+" (removidas)"]+=1
    L=[res[i] for i in ordem if i in res]
    if B is None and not L: continue
    f=open(f"{repo}/{p}","w")
    json.dump(L,f,ensure_ascii=False) if compacto else json.dump(L,f,ensure_ascii=False,indent=0)
print("mudanças por ramo:",dict(tot)); print("conflitos de verdade:",conflitos[:20],len(conflitos))
sys.exit(1 if conflitos else 0)
