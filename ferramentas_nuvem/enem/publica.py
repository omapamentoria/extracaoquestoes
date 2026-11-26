# Grava no Banco-de-questoes a prova inteira do ENEM (saida do integra.py), sem mexer no texto das questoes que ja existem.
#  - questao que ja estava no banco: mesmo id, texto, imagens, comentario e classificacao; passa a ter o numero, o arquivo e
#    os campos da prova completa da cor escolhida (prova_completa, prova_completa_cor, prova_completa_ordem);
#    se o gabarito oficial da cor escolhida for diferente, vale o oficial e o comentario sai (lista a refazer).
#  - questao nova: id novo (depois do maior id do banco), imagens em WebP em imagens/, parte banco_parte_28.json em diante.
# Uso: publica.py <Banco-de-questoes> <correcoes.json> <int_*.json>...
import json,glob,os,re,sys,cv2,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from espacos import Espacos
DEST,CORR=sys.argv[1:3]; INTS=sys.argv[3:]
R="/home/user/extracaoquestoes"
CAT={d["id"]:d for d in json.load(open(R+"/_banco/catalogo_debug.json"))}
corr=json.load(open(CORR)) if os.path.exists(CORR) else {}
PARTES=sorted(glob.glob(DEST+"/final/partes/banco_parte_*.json"))
dados={f:json.load(open(f)) for f in PARTES}
fmt={f:(open(f).read().count("\n")<=1) for f in PARTES}     # True = compacto numa linha
idx={q["id"]:(f,q) for f in PARTES for q in dados[f]}
prox=max(idx)+1
VAZIO={"passos_raciocinio":[],"analise_correta_titulo":"","analise_correta_texto":"","analise_incorretas_intro":"","analise_incorretas":[],
       "quadro_resumo":[],"leve_para_prova":"","flashcards":[]}
def area_cod(t):
    t=(t or "").upper()
    return "naturezas" if "NATUREZA" in t else "humanas" if "HUMANAS" in t else "exatas" if "MATEM" in t else "linguagens" if "LINGUAGENS" in t else ""
def aplica(r):
    c=corr.get(r["origem_texto"])
    if not c: return
    for a,b in c.get("statement_sub",[]):
        n=re.subn(a,b,r["statement"]); assert n[1]==1,(r["origem_texto"],a); r["statement"]=n[0]
    for L,(a,b) in c.get("alt_sub",{}).items():
        for x in r["alternativas"]:
            if x["letra"]==L: n=re.subn(a,b,x["texto"]); assert n[1]==1,(r["origem_texto"],L); x["texto"]=n[0]
    for L,t in c.get("alternativas",{}).items():
        for x in r["alternativas"]:
            if x["letra"]==L: x["texto"]=t
    r["alertas"]=[]
def webp(src,nome):
    os.makedirs(DEST+"/imagens",exist_ok=True); alvo=DEST+"/imagens/"+nome
    im=cv2.imread(src,cv2.IMREAD_UNCHANGED)
    if im.ndim==3 and im.shape[2]==4: a=im[:,:,3:4]/255.0; im=(im[:,:,:3]*a+255*(1-a)).astype("uint8")
    if im.shape[1]>1000: im=cv2.resize(im,(1000,max(1,int(im.shape[0]*1000/im.shape[1]))),interpolation=cv2.INTER_AREA)
    assert cv2.imwrite(alvo,im,[cv2.IMWRITE_WEBP_QUALITY,85]); return nome
nova_parte=DEST+"/final/partes/banco_parte_28.json"
if nova_parte not in dados: dados[nova_parte]=[]; fmt[nova_parte]=True
rel=collections.Counter(); refazer=[]; novos_ids=[]; mexidos={nova_parte}; espacadas=[]
for ij in INTS:
    d=json.load(open(ij)); c=CAT[d["pid"]]; ESP=Espacos(R+"/"+c["caminho"])
    for a,b,nome_area in corr.get("_area",{}).get(d["pid"],[]):
        for r in d["novas"]+[x["registro"] for x in d["casadas"]]:
            if a<=r["numero"]<=b: r["area_prova"]=nome_area
    cont=collections.Counter(r["area_prova"] for r in d["novas"]+[x["registro"] for x in d["casadas"]])
    assert all(v in (45,50) for v in cont.values()), ("áreas com contagem estranha",d["pid"],cont)
    def esp(q):
        k=0
        for campo in ("statement","apos_alternativas"):
            q[campo],n=ESP.corrige(q.get(campo) or ""); k+=n
        for a in q["alternativas"]: a["texto"],n=ESP.corrige(a["texto"]); k+=n
        return k
    nome=f"ENEM {c['ano']} {c['edicao']} - dia {c['dia']} - caderno {c['caderno']}"
    def num(r): return f"{r['numero']}-{'ING' if r['idioma']=='inglês' else 'ESP'}" if r["idioma"] else str(r["numero"])
    def campos(r): return {"number":num(r),"prova":c["arquivo"],"origem_texto":r["origem_texto"],"prova_completa":nome,
                           "prova_completa_cor":c["caderno"],"prova_completa_ordem":r["numero"]}
    for x in d["casadas"]:
        f,q=idx[x["id_banco"]]; r=x["registro"]
        q.update(campos(r)); rel["atualizadas"]+=1; mexidos.add(f)
        if r["area_prova"] and q.get("area_prova")!=r["area_prova"]: rel["area_prova corrigida"]+=1; q["area_prova"]=r["area_prova"]
        if esp(q): rel["publicadas com palavras grudadas corrigidas"]+=1; espacadas.append(q["id"])
        if q["gabarito"]!=r["gabarito"]:
            refazer.append({"id":q["id"],"gabarito":r["gabarito"],"gabarito_antigo":q["gabarito"],"motivo":f"gabarito oficial do {nome}",
                            "tinha_comentario":bool(q.get("analise_correta_texto"))})
            q["gabarito"]=r["gabarito"]; q.update(json.loads(json.dumps(VAZIO))); rel["gabarito corrigido"]+=1
    for r in d["novas"]:
        aplica(r); esp(r)
        assert not any("PENDENTE" in a for a in r["alertas"]), r["origem_texto"]
        assert "(cid:" not in json.dumps(r,ensure_ascii=False), r["origem_texto"]
        nid=prox; prox+=1; novos_ids.append(nid)
        imgs=[webp(s,f"{nid}_{k}.webp") for k,s in enumerate(r["imagens_src"],1)]
        q={"id":nid,"exam":"ENEM","prova":c["arquivo"],"ano":str(c["ano"]),"number":num(r),"subject":"","tema_n1":"","tema_n2":"","tema_n3":"","tema_n4":"",
           "statement":r["statement"],"fontes":r["fontes"],"alternativas":r["alternativas"],"apos_alternativas":r["apos_alternativas"],
           "gabarito":r["gabarito"],"tem_imagem":"sim" if imgs else "nao","imagens":imgs,"url":"","vestibular":"ENEM","edicao":c["edicao"],
           "dia":str(c["dia"]),"formato":"objetiva","tipo_prova":"oficial","instituicao":"","simulado_n":"","area_prova":r["area_prova"],
           "idioma":r["idioma"],"origem_texto":r["origem_texto"],**json.loads(json.dumps(VAZIO)),"nota_revisao":None,
           "area_codigo":area_cod(r["area_prova"]),"materia_codigo":"","assunto_codigo":"","subassunto_codigo":""}
        q.update(campos(r)); dados[nova_parte].append(q); rel["novas"]+=1
for f,L in dados.items():
    if f not in mexidos: continue
    if fmt[f]: json.dump(L,open(f,"w"),ensure_ascii=False)
    else: json.dump(L,open(f,"w"),ensure_ascii=False,indent=0)
json.dump({"novos_ids":novos_ids,"refazer":refazer,"espacadas":espacadas},open(DEST+"/../publica_saida.json","w"),ensure_ascii=False,indent=0)
print(dict(rel),"ids novos",novos_ids[:1],"…",novos_ids[-1:])
