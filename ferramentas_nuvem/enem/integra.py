# Prova inteira do ENEM: monta as questoes da cor escolhida no formato do banco e casa com as que ja estao publicadas.
# Uso: integra.py <partes_dir> <pasta_extracao Pxxxx> <saida.json>
# Saida: {"casadas":[{novo,id_banco,sim,...}], "novas":[registro no formato do banco sem id], "banco_sem_par":[ids]}
import json,glob,re,sys,os,difflib,collections
P,D,OUT=sys.argv[1:4]
R="/home/user/extracaoquestoes"
CAT={d["id"]:d for d in json.load(open(R+"/_banco/catalogo_debug.json"))}
pid=os.path.basename(D.rstrip("/")); c=CAT[pid]
qs=json.load(open(D+"/questoes.json"))
bases={t["id"]:t for t in json.load(open(D+"/textos_base.json"))} if os.path.exists(D+"/textos_base.json") else {}
def monta(q):
    partes=[bases[b] for b in (q.get("textos_base_ids") or []) if b in bases]+[q]
    imgs,fontes,txt=[],[],[]
    for k,p in enumerate(partes):
        mi,mf={},{}
        for im in p.get("imagens",[]): imgs.append(os.path.join(D,im["arquivo"])); mi[str(im["id"])]=len(imgs)
        for j,fo in enumerate(p.get("fontes",[]),1): fontes.append(fo); mf[str(j)]=len(fontes)
        sub=lambda t,mi=mi,mf=mf: re.sub(r"\{\{fonte:(\d+)\}\}",lambda m:"{{fonte:%s}}"%mf.get(m.group(1),m.group(1)),
                 re.sub(r"\{\{img:(\d+)\}\}",lambda m:"{{img:%s}}"%mi.get(m.group(1),m.group(1)),t or ""))
        txt.append(sub(p.get("texto") if k<len(partes)-1 else p["enunciado"]))
        if k==len(partes)-1: ult=sub
    alts=[{"letra":a["letra"],"texto":ult(a["texto"])} for a in q["alternativas"]]
    return "\n\n".join(txt).strip(),alts,ult(q.get("apos_alternativas","")),fontes,imgs
norm=lambda s:re.sub(r"\s+"," ",re.sub(r"<[^>]+>|\{\{[^}]+\}\}|[*_\\]","",s or "").lower()).strip()
chave=lambda st,al:norm(st)+" || "+" | ".join(norm(a["texto"]) for a in al)
banco=[q for f in sorted(glob.glob(P+"/*.json")) for q in json.load(open(f))
       if q.get("vestibular")=="ENEM" and q.get("tipo_prova")!="simulado" and str(q.get("ano"))==str(c["ano"])
       and str(q.get("dia"))==str(c["dia"]) and (q.get("edicao") or "")==c["edicao"]]
reg=[]
for q in qs:
    st,al,apos,fo,im=monta(q)
    reg.append({"origem_texto":q["id"],"numero":q["numero"],"idioma":q.get("idioma"),"statement":st,"alternativas":al,"apos_alternativas":apos,
                "fontes":fo,"imagens_src":im,"gabarito":"anulada" if q.get("anulada") else q["gabarito"],"area_prova":q.get("area") or "",
                "alertas":q.get("alertas",[])})
# casamento guloso pela maior semelhanca (pares unicos)
cand=[]
for i,r in enumerate(reg):
    kr=chave(r["statement"],r["alternativas"])
    for q in banco:
        if r["idioma"] and q.get("idioma") and r["idioma"]!=q["idioma"]: continue
        s=difflib.SequenceMatcher(None,kr,chave(q["statement"],q["alternativas"]),autojunk=False)
        if s.real_quick_ratio()<0.5 or s.quick_ratio()<0.6: continue
        cand.append((s.ratio(),i,q["id"]))
cand.sort(reverse=True); usado_r,usado_b,par={}, set(),{}
B={q["id"]:q for q in banco}
for s,i,b in cand:
    if s<0.80 or i in usado_r or b in usado_b: continue
    usado_r[i]=1; usado_b.add(b); par[i]=(b,s)
casadas=[];novas=[]
for i,r in enumerate(reg):
    if i in par:
        b,s=par[i]; q=B[b]
        casadas.append({"origem_texto":r["origem_texto"],"numero":r["numero"],"idioma":r["idioma"],"id_banco":b,"num_banco":q["number"],"sim":round(s,3),
                        "gab_oficial":r["gabarito"],"gab_banco":q["gabarito"],"tem_coment":bool(q.get("analise_correta_texto")),
                        "imgs_novo":len(r["imagens_src"]),"imgs_banco":len(q.get("imagens") or []),"registro":r})
    else: novas.append(r)
json.dump({"pid":pid,"cor":c["caderno"],"casadas":casadas,"novas":novas,"banco_sem_par":sorted(set(B)-usado_b)},open(OUT,"w"),ensure_ascii=False,indent=0)
print(pid,c["arquivo"],"| extraidas",len(reg),"| no banco",len(banco),"| casadas",len(casadas),"| novas",len(novas),"| banco sem par",len(B)-len(usado_b))
print("  gabarito diferente do banco:",[(x["numero"],x["id_banco"],x["gab_banco"],"->",x["gab_oficial"]) for x in casadas if x["gab_banco"]!=x["gab_oficial"]])
print("  semelhanca < 0.97:",[(x["numero"],x["id_banco"],x["sim"]) for x in casadas if x["sim"]<0.97])
print("  numero de imagens diferente:",[(x["numero"],x["id_banco"],x["imgs_banco"],x["imgs_novo"]) for x in casadas if x["imgs_banco"]!=x["imgs_novo"]])
print("  banco sem par:",sorted(set(B)-usado_b))
