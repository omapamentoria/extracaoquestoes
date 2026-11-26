# Correcoes feitas a mao (correcoes/<ano>.json): carregar e aplicar numa questao montada pelo integra.py
import json,re
def carrega(caminhos):
    corr={}
    for _c in caminhos.split(","):
        for k,v in json.load(open(_c)).items():
            if k in ("_area","_casa"): corr.setdefault(k,{}).update(v)
            else: corr[k]=v
    return corr
def aplica(r,corr):
    c=corr.get(r["origem_texto"])
    if not c: return
    for a,b in c.get("statement_sub",[]):
        n=re.subn(a,lambda m,b=b:b,r["statement"]); assert n[1]==1,(r["origem_texto"],a); r["statement"]=n[0]
    for L,(a,b) in c.get("alt_sub",{}).items():
        for x in r["alternativas"]:
            if x["letra"]==L: n=re.subn(a,lambda m,b=b:b,x["texto"]); assert n[1]==1,(r["origem_texto"],L); x["texto"]=n[0]
    for L,t in c.get("alternativas",{}).items():
        for x in r["alternativas"]:
            if x["letra"]==L: x["texto"]=t
    r["alertas"]=[]
