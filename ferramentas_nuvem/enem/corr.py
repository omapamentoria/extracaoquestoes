# Correcoes feitas a mao (correcoes/<ano>.json): carregar e aplicar numa questao montada pelo integra.py
import json,re
def carrega(caminhos):
    corr={}
    for _c in caminhos.split(","):
        for k,v in json.load(open(_c)).items():
            if k in ("_area","_casa","_pares","_par","_edicao_banco"): corr.setdefault(k,{}).update(v)
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
    if "alternativas_lista" in c:   # lista inteira (quando o extrator criou alternativas a mais, ex.: itens a), b), c) do texto)
        r["alternativas"]=[{"letra":L,"texto":t} for L,t in c["alternativas_lista"]]
    for L,t in c.get("alternativas",{}).items():
        for x in r["alternativas"]:
            if x["letra"]==L: x["texto"]=t
    if "remove_imagens" in c:   # imagem que e pedaco de formula ja transcrita: sai e as outras sao renumeradas
        fica=[k for k in range(1,len(r["imagens_src"])+1) if k not in c["remove_imagens"]]; nova={str(k):str(j) for j,k in enumerate(fica,1)}
        r["imagens_src"]=[r["imagens_src"][k-1] for k in fica]
        ren=lambda t:re.sub(r"\{\{img:(\d+)\}\}",lambda m:"{{img:%s}}"%nova[m.group(1)] if m.group(1) in nova else "",t)
        r["statement"]=ren(r["statement"]); r["apos_alternativas"]=ren(r.get("apos_alternativas",""))
        for x in r["alternativas"]: x["texto"]=ren(x["texto"])
    if "imagens_extra" in c:   # recortes da pagina feitos a mao (alternativa desenhada sem imagem): {{imgx:N}} = N-esimo recorte
        base=len(r["imagens_src"]); r["imagens_src"]=r["imagens_src"]+list(c["imagens_extra"])
        cv=lambda t:re.sub(r"\{\{imgx:(\d+)\}\}",lambda m:"{{img:%d}}"%(base+int(m.group(1))),t or "")
        r["statement"]=cv(r["statement"]); r["apos_alternativas"]=cv(r.get("apos_alternativas",""))
        for x in r["alternativas"]: x["texto"]=cv(x["texto"])
    if "apos_alternativas" in c: r["apos_alternativas"]=c["apos_alternativas"]
    if "fontes" in c: r["fontes"]=c["fontes"]
    r["alertas"]=[]
