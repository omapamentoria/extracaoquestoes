# Ajustes feitos a mao na EXTRACAO (antes do integra.py), para o que o correcoes/<ano>.json nao alcanca:
# alternativas que o extrator nao achou (formula desenhada, letra em bolinha desenhada), alternativas que sao figuras
# (recortadas da pagina do PDF, uma por letra) e enunciado embaralhado (reescrito lendo a imagem da pagina).
# Uso: ajusta_extracao.py <correcoes/<ano>_extracao.json>     (rodar de novo depois de cada nova extracao)
# Formato: {"<id da questao>": {"motivo": "...", "enunciado": texto inteiro | "enunciado_sub": [[regex, texto]],
#           "alternativas": {"A": "..."} , "alt_imagens": "auto", "imagens": [ids que ficam]}}
import json,os,re,sys,subprocess,glob
import pdfplumber,cv2
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from catalogo import CAT
R="/home/user/extracaoquestoes"; BM=os.path.expanduser("~/mnt/BM")
AJ=json.load(open(sys.argv[1]))
def letras(page,pid=None):
    # letras das alternativas como imagens (ENEM 2012 regular): caixas de _banco/bolhas/<PID>.json (bolhas_img.py)
    bj=os.path.join(R,"_banco","bolhas",(pid or "")+".json")
    if pid and os.path.exists(bj):
        bl=json.load(open(bj)).get(str(page.page_number),[])
        if bl: return [{"text":b[4],"x0":b[0],"top":b[1],"x1":b[2],"bottom":b[3]} for b in bl]
    ws=page.extract_words(extra_attrs=["fontname","size"])
    # letra em negrito ou em fonte de bolinha do ENEM (BundesbahnPi, dingbats)
    return [w for w in ws if re.fullmatch(r"[A-E]",w["text"]) and ("Bold" in w["fontname"] or re.search(r"(?i)bundesbahn|dingbat|zapf",w["fontname"]))]
def recorta(pid,q,d):
    pdf=pdfplumber.open(os.path.join(BM,CAT[pid]["caminho"])); achou={}
    for pg in q["paginas"]:
        p=pdf.pages[pg-1]; ls=letras(p,pid)
        # so as letras dentro da area da questao nesta pagina (caixas de texto + figuras): outra questao na mesma pagina fica fora
        bx=[c for c in q.get("caixas",{}).get(str(pg),[])]+[i["bbox"] for i in q["imagens"] if i.get("pagina")==pg]
        if bx:
            X0=min(b_[0] for b_ in bx)-25; X1=max(b_[2] for b_ in bx); Y0=min(b_[1] for b_ in bx)-5; Y1=max(b_[3] for b_ in bx)+20
            ls=[w for w in ls if X0<=w["x0"]<=X1 and Y0<=w["top"]<=Y1]
        # so as letras que comecam alternativa: em coluna (mesmo x0 de outra letra) e abaixo do enunciado
        for w in ls:
            if w["text"] in achou: continue
            col=[v for v in ls if abs(v["x0"]-w["x0"])<3]
            if len(col)<2 and not any(abs(v["top"]-w["top"])<3 and v is not w for v in ls): continue
            achou[w["text"]]=(pg,w,ls,p)
    falta=[L for L in "ABCDE" if L not in achou]
    if len(falta)==1 and falta[0] not in "AE":
        # letra sem texto no PDF (bolinha vazia): fica no meio das vizinhas da mesma coluna (alternativas igualmente espacadas)
        L=falta[0]; a_=achou[chr(ord(L)-1)]; b_=achou[chr(ord(L)+1)]
        if a_[0]==b_[0] and abs(a_[1]["x0"]-b_[1]["x0"])<3:
            w=dict(a_[1]); w["text"]=L; w["top"]=(a_[1]["top"]+b_[1]["top"])/2; w["bottom"]=w["top"]+a_[1]["bottom"]-a_[1]["top"]
            a_[2].append(w); achou[L]=(a_[0],w,a_[2],a_[3]); print(q["id"],"letra",L,"sem texto no PDF: posição pelo meio das vizinhas")
    assert sorted(achou)==list("ABCDE"),(q["id"],sorted(achou))
    imgs=[]
    for L in "ABCDE":
        pg,w,ls,p=achou[L]
        dir_=[v["x0"] for v in ls if v["x0"]>w["x0"]+30]; x1=min(dir_)-6 if dir_ else p.width-30
        abaixo=[v["top"] for v in ls if abs(v["x0"]-w["x0"])<3 and v["top"]>w["top"]+5]
        # fim da caixa: proxima letra da coluna, ou o fim do desenho da pagina
        if abaixo: y1=min(abaixo)-3
        else:
            objs=[o for o in p.objects.get("curve",[])+p.objects.get("line",[])+p.objects.get("rect",[])+p.chars if o["top"]>w["top"] and w["x0"]-5<=o["x0"]<=x1]
            objs=[o for o in objs if o["bottom"]-o["top"]<p.height*0.5]
            objs+= [o for o in p.images if o["top"]>w["top"]-5 and o["x1"]>w["x0"] and o["x0"]<x1]
            y1=max([o["bottom"] for o in objs if o["bottom"]<p.height-40]+[w["bottom"]+20])+4
            acima=[v["top"] for v in ls if abs(v["x0"]-w["x0"])<3 and v["top"]<w["top"]-5]
            if acima: y1=max(y1,min(w["top"]+(w["top"]-max(acima))-3,p.height-8))   # alternativas da coluna tem a mesma altura
        x0=w["x1"]+4; y0=w["top"]-4
        arq="img/%s_alt%s.png"%(q["id"].split("-",1)[1],L)
        im=p.crop((x0,y0,x1,y1)).to_image(resolution=200); im.save(os.path.join(d,arq))
        # tira a margem branca
        g=cv2.imread(os.path.join(d,arq),0); ys,xs=(g<230).nonzero()
        if len(xs): cv2.imwrite(os.path.join(d,arq),g[max(0,ys.min()-6):ys.max()+7,max(0,xs.min()-6):xs.max()+7])
        imgs.append((L,arq,pg,[x0,y0,x1,y1]))
    return imgs
por_pid={}
for k in AJ:
    if not k.startswith("_"): por_pid.setdefault(k.split("-")[0],[]).append(k)
for pid in AJ.get("_faixas",[])+list(AJ.get("_idioma",{})): por_pid.setdefault(pid,[])
def tira_faixas(q):
    """faixa decorativa "enem2020enem2020..." ao lado do titulo "Questao N" (provas de 2020), lida como figura:
    imagem muito baixa e comprida. Sai a imagem e a marca {{img:N}} dela."""
    fx=[i for i in q["imagens"] if i["bbox"][3]-i["bbox"][1]<12 and (i["bbox"][2]-i["bbox"][0])>15*(i["bbox"][3]-i["bbox"][1])]
    for i in fx:
        m="{{img:%d}}"%i["id"]
        for campo,obj in [("enunciado",q),("apos_alternativas",q)]+[("texto",a) for a in q["alternativas"]]:
            if m in (obj.get(campo) or ""): obj[campo]=re.sub(r"\n*"+re.escape(m)+r"\n*","\n\n",obj[campo]).strip()
    q["imagens"]=[i for i in q["imagens"] if i not in fx]
    return len(fx)
for pid,ks in por_pid.items():
    d=glob.glob(f"{R}/_banco/questoes/*/*/{pid}")[0]; f=d+"/questoes.json"; qs=json.load(open(f))
    # pode rodar de novo: guarda a extracao crua (sem ajuste) e sempre parte dela; extracao nova (sem nenhum
    # "ajuste à mão") substitui a copia guardada
    cru=d+"/revisao/questoes_sem_ajuste.json"
    if any(a_.startswith("ajuste à mão") for q in qs for a_ in q.get("alertas",[])):
        assert os.path.exists(cru),(pid,"ajustada sem copia crua: extrair de novo"); qs=json.load(open(cru))
    else: os.makedirs(d+"/revisao",exist_ok=True); json.dump(qs,open(cru,"w"),ensure_ascii=False)
    idx={q["id"]:q for q in qs}
    for a_,b_,idi in AJ.get("_idioma",{}).get(pid,[]):   # caderno so com uma lingua estrangeira (digital 2020: so ingles), sem marca de idioma
        for q in qs:
            if a_<=q["numero"]<=b_ and not q.get("idioma"): q["idioma"]=idi
    if pid in AJ.get("_faixas",[]): print(pid,"faixas decorativas retiradas:",sum(tira_faixas(q) for q in qs))
    for k in ks:
        a=AJ[k]; q=idx[k]
        if "enunciado" in a: q["enunciado"]=a["enunciado"]
        for x,y in a.get("enunciado_sub",[]):
            q["enunciado"],n=re.subn(x,lambda m,y=y:y,q["enunciado"]); assert n==1,(k,x)
        if "fontes" in a: q["fontes"]=a["fontes"]
        if "imagens" in a: q["imagens"]=[i for i in q["imagens"] if i["id"] in a["imagens"]]
        for n_ in a.get("imagens_novas",[]):   # figura recortada de novo da pagina (a do extrator saiu incompleta)
            src_=q["texto_de"].split()[0] if q.get("texto_de") else pid   # prova montada com o texto de outra cor: recorta do PDF com texto
            pdf_=pdfplumber.open(os.path.join(BM,CAT[src_]["caminho"])); arq="img/%s_nova%d.png"%(k.split("-",1)[1],n_["id"])
            pdf_.pages[n_["pagina"]-1].crop(tuple(n_["bbox"])).to_image(resolution=200).save(os.path.join(d,arq))
            q["imagens"].append({"id":n_["id"],"arquivo":arq,"pagina":n_["pagina"],"bbox":n_["bbox"]})
        alts=dict(a.get("alternativas",{}))
        if a.get("alt_imagens")=="auto":
            nid=max([i["id"] for i in q["imagens"]]+[0])
            for L,arq,pg,bb in recorta(pid,q,d):
                nid+=1; q["imagens"].append({"id":nid,"arquivo":arq,"pagina":pg,"bbox":[round(v,1) for v in bb]}); alts[L]="{{img:%d}}"%nid
        if alts:
            assert sorted(alts)==list("ABCDE"),k
            q["alternativas"]=[{"letra":L,"texto":alts[L]} for L in "ABCDE"]
        if "gabarito_oficial" in a: q["gabarito"]=a["gabarito_oficial"]   # conferido depois pelo gab_enem.py (leitura independente)
        q["formato"]="objetiva"; q["gabarito_discursivo"]=None; q["itens"]=[]
        usados={int(m) for m in re.findall(r"\{\{img:(\d+)\}\}",q["enunciado"]+" ".join(x["texto"] for x in q["alternativas"])+q.get("apos_alternativas",""))}
        assert usados=={i["id"] for i in q["imagens"]},(k,"imagens",usados,[i["id"] for i in q["imagens"]])
        assert len(q["alternativas"])==5 and "**A**" not in q["enunciado"],k
        q["alertas"]=[x for x in q["alertas"] if not ("PENDENTE" in x or "alternativa" in x or "letras fora de ordem" in x or "gabarito discursivo" in x or "texto curto solto" in x)]+["ajuste à mão: "+a["motivo"]]
        print(k,"ok")
    json.dump(qs,open(f,"w"),ensure_ascii=False,indent=1)
