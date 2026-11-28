# Prova inteira do ENEM: monta as questoes da cor escolhida no formato do banco e casa com as que ja estao publicadas.
# Uso: integra.py <partes_dir> <pasta_extracao Pxxxx> <saida.json>
# Saida: {"casadas":[{novo,id_banco,sim,...}], "novas":[registro no formato do banco sem id], "banco_sem_par":[ids]}
import json,glob,re,sys,os,difflib,collections
P,D,OUT=sys.argv[1:4]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import corr as _corr
CORR=_corr.carrega(sys.argv[4]) if len(sys.argv)>4 else {}
R="/home/user/extracaoquestoes"
from catalogo import CAT
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
norm=lambda s:re.sub(r"\W+","",re.sub(r"<[^>]+>|\{\{[^}]+\}\}|\\[()]","",s or "").lower())   # so letras e numeros: ignora espacos, grudadas e marcacao
chave=lambda st,al:norm(st)[-1500:]+"|"+"|".join(norm(a["texto"]) for a in al)
PROPRIO_DESDE=121560   # ids criados por esta frente (provas completas): numa nova rodada sao refeitos, nao casados
def candidato(q):
    if q["id"]>=PROPRIO_DESDE and (q.get("origem_texto") or "").startswith(pid+"-"): return False
    if q["id"]<10000:   # banco antigo (FPS/SSA/ENEM de site), sem vestibular/edicao: mesmo ano, qualquer aplicacao
        return q.get("exam")=="ENEM" and str(q.get("ano"))==str(c["ano"])
    # correcoes "_edicao_banco": {"<pid>": ["edicao errada no banco", ...]}: questoes publicadas com a edicao trocada
    # (ex.: 2016 "2ª aplicação" publicada como "PPL/reaplicação") tambem sao candidatas; o publica.py corrige a edicao
    ed_ok=[c["edicao"]]+list(CORR.get("_edicao_banco",{}).get(pid,[]))
    return (q.get("vestibular")=="ENEM" and q.get("tipo_prova")!="simulado" and str(q.get("ano"))==str(c["ano"])
            and str(q.get("dia"))==str(c["dia"]) and (q.get("edicao") or "") in ed_ok)
banco=[q for f in sorted(glob.glob(P+"/*.json")) for q in json.load(open(f)) if candidato(q)]
reg=[]
for q in qs:
    st,al,apos,fo,im=monta(q)
    reg.append({"origem_texto":q["id"],"numero":q["numero"],"idioma":q.get("idioma"),"statement":st,"alternativas":al,"apos_alternativas":apos,
                "fontes":fo,"imagens_src":im,"gabarito":"anulada" if q.get("anulada") else q["gabarito"],"area_prova":q.get("area") or "",
                "alertas":q.get("alertas",[])})
    if q["id"] in CORR: import copy; rr=copy.deepcopy(reg[-1]); _corr.aplica(rr,CORR); reg[-1]["_chave"]=(rr["statement"],rr["alternativas"])
# casamento guloso pela maior semelhanca (pares unicos)
cand=[]
def grams(k): return {k[i:i+6] for i in range(0,max(1,len(k)-5))}   # todos os pedacos: amostrar de 3 em 3 falhava quando um titulo a mais deslocava o texto
BK={q["id"]:chave(q["statement"],q["alternativas"]) for q in banco}; BG={i:grams(k) for i,k in BK.items()}
for i,r in enumerate(reg):
    kr=chave(*r.get("_chave",(r["statement"],r["alternativas"]))); gr={kr[i:i+6] for i in range(max(1,len(kr)-5))}
    # pedacos do novo em todas as posicoes (um titulo a mais no inicio desalinha os pedacos de 3 em 3 e a questao sumia do filtro)
    pre=sorted(banco,key=lambda q:-len(gr&BG[q["id"]])/max(1,len(BG[q["id"]])))[:4]   # 4 mais parecidas pelos pedacos de texto
    for q in pre:
        if r["idioma"] and q.get("idioma") and r["idioma"]!=q["idioma"]: continue
        cand.append((difflib.SequenceMatcher(None,kr,BK[q["id"]],autojunk=False).ratio(),i,q["id"]))
# casamento manual (correcoes: "_casa": {"<id da extracao>": [id_banco, "motivo"]}), para quando o texto antigo e
# incompleto (ex.: site sem a tabela) e a semelhanca fica abaixo do corte
FORCA={k:v[0] for k,v in CORR.get("_casa",{}).items()}
for i,r in enumerate(reg):
    if r["origem_texto"] in FORCA and FORCA[r["origem_texto"]] in BK:
        b=FORCA[r["origem_texto"]]; kr=chave(*r.get("_chave",(r["statement"],r["alternativas"])))
        cand=[c_ for c_ in cand if c_[1]!=i and c_[2]!=b]+[(2+difflib.SequenceMatcher(None,kr,BK[b],autojunk=False).ratio(),i,b)]
cand.sort(reverse=True); usado_r,usado_b,par={}, set(),{}
B={q["id"]:q for q in banco}
# pares forcados a mao (correcoes/<ano>.json, "_pares": {"Pxxxx-Qnnn": id_banco}), quando o banco antigo tem alternativas trocadas
for i,r in enumerate(reg):
    b=(CORR.get("_pares") or {}).get(r["origem_texto"])
    if b is not None and b in B:
        kr=chave(*r.get("_chave",(r["statement"],r["alternativas"])))
        usado_r[i]=1; usado_b.add(b); par[i]=(b,difflib.SequenceMatcher(None,kr,BK[b],autojunk=False).ratio())
# par forcado (correcoes "_par": {"<questao extraida>": id_no_banco}): questao do banco com texto vazio, que nao casa pelo texto
for i,r in enumerate(reg):
    b=CORR.get("_par",{}).get(r["origem_texto"])
    if b in B and b not in usado_b and i not in usado_r: usado_r[i]=1; usado_b.add(b); par[i]=(b,1.0)
for s,i,b in cand:
    if s<0.80 or i in usado_r or b in usado_b: continue
    usado_r[i]=1; usado_b.add(b); par[i]=(b,s-2 if s>=2 else s)
casadas=[];novas=[]
for i,r in enumerate(reg):
    if i in par:
        b,s=par[i]; q=B[b]
        casadas.append({"origem_texto":r["origem_texto"],"numero":r["numero"],"idioma":r["idioma"],"id_banco":b,"num_banco":q["number"],"sim":round(s,3),
                        "gab_oficial":r["gabarito"],"gab_banco":q["gabarito"],"tem_coment":bool(q.get("analise_correta_texto")),
                        "imgs_novo":len(r["imagens_src"]),"imgs_banco":len(q.get("imagens") or []),"registro":r})
    else: novas.append(r)
antigos_sem_par=sorted(i for i in set(B)-usado_b if i<10000); novos_sem_par=sorted(i for i in set(B)-usado_b if i>=10000)
json.dump({"pid":pid,"cor":c["caderno"],"casadas":casadas,"novas":novas,"banco_sem_par":novos_sem_par,"antigos_sem_par":antigos_sem_par},open(OUT,"w"),ensure_ascii=False,indent=0)
print(pid,c["arquivo"],"| extraidas",len(reg),"| candidatas no banco",len(banco),"| casadas",len(casadas),"(do banco antigo",sum(x["id_banco"]<10000 for x in casadas),") | novas",len(novas),"| sem par (extração nova)",len(novos_sem_par))
print("  gabarito diferente do banco:",[(x["numero"],x["id_banco"],x["gab_banco"],"->",x["gab_oficial"]) for x in casadas if x["gab_banco"]!=x["gab_oficial"]])
print("  semelhanca < 0.97:",[(x["numero"],x["id_banco"],x["sim"]) for x in casadas if x["sim"]<0.97])
print("  numero de imagens diferente:",[(x["numero"],x["id_banco"],x["imgs_banco"],x["imgs_novo"]) for x in casadas if x["imgs_banco"]!=x["imgs_novo"]])
print("  sem par (extração nova, mesma aplicação):",novos_sem_par)
