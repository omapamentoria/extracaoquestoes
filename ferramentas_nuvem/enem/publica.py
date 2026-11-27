# Grava no Banco-de-questoes a prova inteira do ENEM (saida do integra.py), sem mexer no texto das questoes que ja existem.
#  - questao que ja estava no banco: mesmo id, texto, imagens, comentario e classificacao; passa a ter o numero, o arquivo e
#    os campos da prova completa da cor escolhida (prova_completa, prova_completa_cor, prova_completa_ordem);
#    se o gabarito oficial da cor escolhida for diferente, vale o oficial e o comentario sai (lista a refazer).
#  - questao nova: id novo (depois do maior id do banco), imagens em WebP em imagens/, parte banco_parte_28.json em diante.
# Uso: publica.py <Banco-de-questoes> <correcoes.json> <int_*.json>...
import json,glob,os,re,sys,cv2,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from espacos import Espacos
from corr import aplica as _aplica
DEST,CORR=sys.argv[1:3]; INTS=sys.argv[3:]
R="/home/user/extracaoquestoes"
from catalogo import CAT
corr={}
for _c in CORR.split(","):
    for k,v in json.load(open(_c)).items():
        if k in ("_area","_casa","_reextrai"): corr.setdefault(k,{}).update(v)
        else: corr[k]=v
PARTES=sorted(glob.glob(DEST+"/final/partes/banco_parte_*.json"))
dados={f:json.load(open(f)) for f in PARTES}
fmt={f:(open(f).read().count("\n")<=1) for f in PARTES}     # True = compacto numa linha
idx={q["id"]:(f,q) for f in PARTES for q in dados[f]}
PROPRIO_DESDE=121560
prox=max([max(idx)+1,int(os.environ.get("ID_BASE","0"))])
VAZIO={"passos_raciocinio":[],"analise_correta_titulo":"","analise_correta_texto":"","analise_incorretas_intro":"","analise_incorretas":[],
       "quadro_resumo":[],"leve_para_prova":"","flashcards":[]}
def area_cod(t):
    t=(t or "").upper()
    return "naturezas" if "NATUREZA" in t else "humanas" if "HUMANAS" in t else "exatas" if "MATEM" in t else "linguagens" if "LINGUAGENS" in t else ""
def aplica(r): return _aplica(r,corr)
def defeitos(q,imgs=None):
    """defeitos de extracao detectaveis sem olhar o PDF"""
    from espacos import grudadas
    alts=q["alternativas"]; t=json.dumps([q["statement"],alts,q.get("apos_alternativas","")],ensure_ascii=False)
    d=[]
    if "(cid:" in t or re.search(r"[\ue000-\uf8ff]",t): d.append("símbolo sem tradução")
    if grudadas(t): d.append("palavras grudadas")
    if "teXto" in t: d.append("versalete")
    if re.search(r"E SUAS TECNOLOGIAS\s+Questões",t): d.append("título de área no texto")
    if len(alts)!=5 or [a["letra"] for a in alts]!=list("ABCDE"): d.append("alternativas fora do padrão")
    if any(not a["texto"].strip() for a in alts): d.append("alternativa vazia")
    if not re.sub(r"\{\{[^}]+\}\}","",q["statement"]).strip() and not (imgs if imgs is not None else q.get("imagens")): d.append("enunciado vazio")
    if any(re.search(r"(^|\n)\s*\(?[A-E]\)\s+\S",a["texto"]) for a in alts): d.append("alternativa com outra alternativa dentro")
    if re.search(r"\n\s*\(?A\)\s.+\n\s*\(?B\)\s",q["statement"]): d.append("alternativas dentro do enunciado")
    n=len(q.get("imagens") or []) if imgs is None else imgs
    refs={int(x) for x in re.findall(r"\{\{img:(\d+)\}\}",t)}
    if refs!=set(range(1,n+1)): d.append("imagens desencontradas do texto")
    return d
def webp(src,nome):
    os.makedirs(DEST+"/imagens",exist_ok=True); alvo=DEST+"/imagens/"+nome
    im=cv2.imread(src,cv2.IMREAD_UNCHANGED)
    if im.ndim==3 and im.shape[2]==4: a=im[:,:,3:4]/255.0; im=(im[:,:,:3]*a+255*(1-a)).astype("uint8")
    if im.shape[1]>1000: im=cv2.resize(im,(1000,max(1,int(im.shape[0]*1000/im.shape[1]))),interpolation=cv2.INTER_AREA)
    assert cv2.imwrite(alvo,im,[cv2.IMWRITE_WEBP_QUALITY,85]); return nome
nova_parte=DEST+"/final/partes/banco_parte_%s.json"%os.environ.get("PARTE","28")
if nova_parte not in dados: dados[nova_parte]=[]; fmt[nova_parte]=True
proprios={q.get("origem_texto"):(f,q) for f in dados for q in dados[f] if q["id"]>=PROPRIO_DESDE and q.get("prova_completa")}
rel=collections.Counter(); refazer=[]; novos_ids=[]; mexidos={nova_parte}; substituidos=set(); espacadas=[]; reextraidas=[]; ver=[]
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
            q[campo],n=re.subn(r"\bteXto\b","TEXTO",q[campo]); k+=n     # versalete lido errado
        for a in q["alternativas"]: a["texto"],n=ESP.corrige(a["texto"]); k+=n
        return k
    nome=f"ENEM {c['ano']} {c['edicao']} - dia {c['dia']} - caderno {c['caderno']}"
    def num(r): return f"{r['numero']}-{'ING' if r['idioma']=='inglês' else 'ESP'}" if r["idioma"] else str(r["numero"])
    def campos(r): return {"number":num(r),"prova":c["arquivo"],"origem_texto":r["origem_texto"],"prova_completa":nome,
                           "prova_completa_cor":c["caderno"],"prova_completa_ordem":r["numero"]}
    def limpa(r):
        aplica(r); esp(r)
        TIT=r"\s*\*\*(?:LINGUAGENS|CIÊNCIAS|MATEMÁTICA)[^*]{0,60}TECNOLOGIAS\s+Questões de \d+ a \d+\*\*"
        for a in r["alternativas"]:
            a["texto"],n=re.subn(TIT,"",a["texto"]); rel["título de área retirado"]+=n
        r["apos_alternativas"],n=re.subn(TIT,"",r["apos_alternativas"]); rel["título de área retirado"]+=n
        assert not re.search(r"E SUAS TECNOLOGIAS\s+Questões",json.dumps([r["statement"],r["alternativas"]],ensure_ascii=False)),("título de área",r["origem_texto"])
        assert not any("PENDENTE" in a for a in r["alertas"]), r["origem_texto"]
        assert "(cid:" not in json.dumps(r,ensure_ascii=False), r["origem_texto"]
        assert not re.search(r"[\ue000-\uf8ff]",json.dumps({k:r[k] for k in ("statement","alternativas","apos_alternativas")},ensure_ascii=False)), ("símbolo sem tradução",r["origem_texto"])
    def fixos(r): return {"vestibular":"ENEM","exam":"ENEM","ano":str(c["ano"]),"edicao":c["edicao"],"dia":str(c["dia"]),"formato":"objetiva",
                          "tipo_prova":"oficial","idioma":r["idioma"],"area_prova":r["area_prova"]}
    for x in d["casadas"]:
        f,q=idx[x["id_banco"]]; r=x["registro"]
        q.update(campos(r)); rel["atualizadas"]+=1; mexidos.add(f)
        if r["area_prova"] and q.get("area_prova")!=r["area_prova"]: rel["area_prova corrigida"]+=1; q["area_prova"]=r["area_prova"]
        n_esp=esp(q); dv=defeitos(q); limpa(r); dn=defeitos(r,len(r["imagens_src"]))
        # prova marcada em correcoes "_reextrai" (ex.: enfeite do cabecalho publicado como figura): a publicada com imagem
        # a mais que a extracao nova passa a ter o texto e as imagens da extracao nova
        if d["pid"] in corr.get("_reextrai",{}) and x["imgs_banco"]>x["imgs_novo"]: dv=dv+["imagem a mais (enfeite do cabeçalho)"]
        substituidos.add(r["origem_texto"])
        if q["id"]<10000:
            # banco antigo (texto copiado de site, sem PDF): passa a ter o texto e as imagens do PDF oficial da cor escolhida
            imgs=[webp(s_,f"{q['id']}_n{k}.webp") for k,s_ in enumerate(r["imagens_src"],1)]
            q.update({"statement":r["statement"],"alternativas":r["alternativas"],"apos_alternativas":r["apos_alternativas"],"fontes":r["fontes"],
                      "imagens":imgs,"tem_imagem":"sim" if imgs else "nao",**fixos(r)})
            rel["banco antigo: texto do PDF oficial"]+=1
        elif dv and not dn:
            # questao antiga extraida com erro: texto e imagens da extracao nova (mesmo id, gabarito, comentario e classificacao)
            imgs=[webp(s_,f"{q['id']}_n{k}.webp") for k,s_ in enumerate(r["imagens_src"],1)]
            q.update({"statement":r["statement"],"alternativas":r["alternativas"],"apos_alternativas":r["apos_alternativas"],"fontes":r["fontes"],
                      "imagens":imgs,"tem_imagem":"sim" if imgs else "nao"})
            rel["antigas reextraídas"]+=1; reextraidas.append((q["id"],dv))
        elif n_esp: rel["publicadas com palavras grudadas corrigidas"]+=1; espacadas.append(q["id"])
        if dv and dn: rel["antigas com defeito e extração nova também (ver à mão)"]+=1; ver.append((q["id"],dv,dn))
        if q["gabarito"]!=r["gabarito"]:
            refazer.append({"id":q["id"],"gabarito":r["gabarito"],"gabarito_antigo":q["gabarito"],"motivo":"gabarito_corrigido","fonte":f"gabarito oficial do {nome}",
                            "tinha_comentario":bool(q.get("analise_correta_texto"))})
            q["gabarito"]=r["gabarito"]; q.update(json.loads(json.dumps(VAZIO))); rel["gabarito corrigido"]+=1
    for r in d["novas"]:
        limpa(r)
        velho=proprios.get(r["origem_texto"])
        if velho: nid=velho[1]["id"]; rel["novas (id já usado numa rodada anterior)"]+=1
        else: nid=prox; prox+=1
        novos_ids.append(nid)
        imgs=[webp(s,f"{nid}_{k}.webp") for k,s in enumerate(r["imagens_src"],1)]
        q={"id":nid,"exam":"ENEM","prova":c["arquivo"],"ano":str(c["ano"]),"number":num(r),"subject":"","tema_n1":"","tema_n2":"","tema_n3":"","tema_n4":"",
           "statement":r["statement"],"fontes":r["fontes"],"alternativas":r["alternativas"],"apos_alternativas":r["apos_alternativas"],
           "gabarito":r["gabarito"],"tem_imagem":"sim" if imgs else "nao","imagens":imgs,"url":"","vestibular":"ENEM","edicao":c["edicao"],
           "dia":str(c["dia"]),"formato":"objetiva","tipo_prova":"oficial","instituicao":"","simulado_n":"","area_prova":r["area_prova"],
           "idioma":r["idioma"],"origem_texto":r["origem_texto"],**json.loads(json.dumps(VAZIO)),"nota_revisao":None,
           "area_codigo":area_cod(r["area_prova"]),"materia_codigo":"","assunto_codigo":"","subassunto_codigo":""}
        q.update(campos(r)); rel["novas"]+=1
        if velho:
            for k in ("area_codigo","materia_codigo","assunto_codigo","subassunto_codigo"):
                if velho[1].get(k): q[k]=velho[1][k]
            for k in VAZIO:
                if velho[1].get(k) and velho[1].get("gabarito")==q["gabarito"]: q[k]=velho[1][k]
            velho[1].clear(); velho[1].update(q); mexidos.add(velho[0])
        else: dados[nova_parte].append(q)
removidas=[]
for o in substituidos:
    if o in proprios:
        f,q=proprios[o]
        if any(x is q for x in dados[f]) and not any(c_["registro"]["origem_texto"]==o and c_["id_banco"]==q["id"] for ij in INTS for c_ in json.load(open(ij))["casadas"]):
            removidas.append(q["id"]); dados[f]=[x for x in dados[f] if x is not q]; mexidos.add(f)
if removidas: print("REMOVIDAS (cópias de questão que já existia no banco antigo):",len(removidas),sorted(removidas)[:10],"…")
for f,L in dados.items():
    if f not in mexidos: continue
    if fmt[f]: json.dump(L,open(f,"w"),ensure_ascii=False)
    else: json.dump(L,open(f,"w"),ensure_ascii=False,indent=0)
if refazer:   # gabarito trocado pelo oficial: comentario apagado -> lista a refazer (como em outubro)
    arq=DEST+"/final/"+os.environ.get("REFAZER","comentarios_a_refazer_2026-11.json")
    lista=json.load(open(arq)) if os.path.exists(arq) else []
    ja={x["id"] for x in lista}; lista+= [x for x in refazer if x["id"] not in ja]
    json.dump(lista,open(arq,"w"),ensure_ascii=False,indent=0)
    print("COMENTÁRIOS A REFAZER (gabarito corrigido):",[(x["id"],x["gabarito_antigo"],"->",x["gabarito"]) for x in refazer])
json.dump({"novos_ids":novos_ids,"removidas":removidas,"refazer":refazer,"espacadas":espacadas,"reextraidas":reextraidas,"ver":ver},open(DEST+"/../publica_saida.json","w"),ensure_ascii=False,indent=0)
print("reextraídas:",reextraidas); print("ver à mão:",ver)
print(dict(rel),"ids novos",novos_ids[:1],"…",novos_ids[-1:])
