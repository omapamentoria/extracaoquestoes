#!/usr/bin/env python3
# Fabrica v2 (docs/fabrica/ESTRATEGIA_V2.md): roda um lote de provas inteiro SEM IA e grava um relatorio curto.
#   1. baixa   prova e gabarito pelo drive_id (cache local), confere pdfinfo, normaliza MediaBox fora da origem
#   2. extrai  _banco/codigo/06_extrair.py (varias provas ao mesmo tempo)
#   3. gabarito leitura independente do PDF oficial (gab_enem.py ou gab_generico.py): tem que dar 100% igual a extracao;
#              se nao der, a prova fica VERMELHA e nada dela e publicado
#   4. casa    integra.py (casa pelo texto com o banco publicado, inclusive o banco antigo)
#   5. separa  prontas (nenhum alerta, gabarito conferido, texto que casa bem) x pendentes (recorte + texto + motivo em
#              _banco/pendentes/<lote>/<origem>.{png,json})
#   6. classifica as novas pelo vizinho mais parecido (TF-IDF) entre as questoes ja classificadas do banco
#   7. publica so as prontas (publica.py); prova_completa* so quando a prova inteira esta pronta
#   8. verifica (verifica_lote.py) e grava _banco/fabrica/<lote>/relatorio.{md,json}
# Uso: roda_lote.py --lote <nome> [--banco <Banco-de-questoes>] [--paralelo 3] [--reextrai] PID...
#      sem --banco: para depois do passo 6 (nao publica). Variaveis ID_BASE, PARTE, REFAZER: as do publica.py.
import argparse,collections,concurrent.futures as cf,glob,json,os,re,subprocess,sys,time
R="/home/user/extracaoquestoes"; EN=R+"/ferramentas_nuvem/enem"; FA=R+"/ferramentas_nuvem/fabrica"
sys.path[:0]=[EN,FA]
from catalogo import CAT
import corr as _corr
ap=argparse.ArgumentParser(); ap.add_argument("--lote",required=True); ap.add_argument("--banco"); ap.add_argument("--paralelo",type=int,default=3)
ap.add_argument("--reextrai",action="store_true"); ap.add_argument("pids",nargs="+"); A=ap.parse_args()
LOTE=A.lote; PIDS=A.pids
OUTD=f"{R}/_banco/fabrica/{LOTE}"; PEND=f"{R}/_banco/pendentes/{LOTE}"; TMP=f"{R}/_fabrica_tmp/{LOTE}"
for d in (OUTD,PEND,TMP+"/logs"): os.makedirs(d,exist_ok=True)
CORRF=f"{FA}/correcoes/{LOTE}.json"
if not os.path.exists(CORRF): os.makedirs(os.path.dirname(CORRF),exist_ok=True); json.dump({},open(CORRF,"w"))
CORR=_corr.carrega(CORRF)
TEMPO={}; REL={"lote":LOTE,"provas":{}}
def etapa(nome):
    def dec(f):
        def w(*a,**k):
            t=time.time(); print(f"[{time.strftime('%H:%M:%S')}] {nome}...",flush=True); r=f(*a,**k)
            TEMPO[nome]=round(time.time()-t,1); print(f"   {nome}: {TEMPO[nome]} s",flush=True); return r
        return w
    return dec
def sh(cmd,**k): return subprocess.run(cmd,capture_output=True,text=True,**k)
def gab_id(pid): return (CAT[pid].get("gabarito_ids") or "").split()[0] if CAT[pid].get("gabarito_ids") else None
def pasta(pid): c=CAT[pid]; return f"{R}/_banco/questoes/{c['vestibular'] or 'outros'}/{c['ano'] or 'sem_ano'}/{pid}"
def pdf_usado(pid):
    for alt in (f"{R}/_ocr/{pid}.pdf",f"{R}/_norm/{pid}.pdf"):
        if os.path.exists(alt): return alt
    return R+"/"+CAT[pid]["caminho"]
P={pid:{"estado":"verde","motivo":""} for pid in PIDS}   # estado da prova: verde / vermelha

# ---------------------------------------------------------------- 1. baixa
@etapa("baixa")
def baixa():
    def um(p):
        c=CAT[p]; f=R+"/"+c["caminho"]
        if not (os.path.exists(f) and "Pages:" in sh(["pdfinfo",f]).stdout):
            if not c.get("drive_id"): return p,"sem drive_id e sem arquivo"
            os.makedirs(os.path.dirname(f),exist_ok=True)
            sh(["curl","-sL","--retry","3",f"https://drive.usercontent.google.com/download?id={c['drive_id']}&export=download&confirm=t","-o",f])
        inf=sh(["pdfinfo","-box",f]).stdout
        if "Pages:" not in inf: return p,"PDF ilegível (pdfinfo)"
        pg=int(re.search(r"Pages:\s+(\d+)",inf).group(1))
        if c.get("paginas") and int(c["paginas"])!=pg: return p,f"páginas {pg} ≠ catálogo {c['paginas']}"
        mb=re.search(r"MediaBox:\s+([-\d.]+)\s+([-\d.]+)",inf)
        if mb and (abs(float(mb.group(1)))>0.5 or abs(float(mb.group(2)))>0.5) and c.get("papel")=="prova" and not os.path.exists(f"{R}/_norm/{p}.pdf"):
            sh(["python3",EN+"/normaliza_pdf.py",p])
        return p,""
    todos=[x for pid in PIDS for x in [pid,gab_id(pid)] if x]
    with cf.ThreadPoolExecutor(4) as ex:
        for p,err in ex.map(um,todos):
            if err:
                for pid in PIDS:
                    if p in (pid,gab_id(pid)): P[pid].update(estado="vermelha",motivo=f"download/PDF ({p}): {err}")

# ---------------------------------------------------------------- 2. extrai
@etapa("extrai")
def extrai():
    def um(pid):
        if P[pid]["estado"]!="verde": return pid,"pulada"
        if os.path.exists(pasta(pid)+"/questoes.json") and not A.reextrai: return pid,"já extraída (cache)"
        t=time.time(); r=sh(["timeout","1800","python3",R+"/_banco/codigo/06_extrair.py",pid],cwd=R)
        open(f"{TMP}/logs/extrai_{pid}.log","w").write(r.stdout+r.stderr)
        if r.returncode or not os.path.exists(pasta(pid)+"/questoes.json"):
            P[pid].update(estado="vermelha",motivo="extrator falhou (ver log)"); return pid,"FALHOU"
        return pid,f"{time.time()-t:.0f} s"
    with cf.ThreadPoolExecutor(A.paralelo) as ex:
        for pid,s in ex.map(um,PIDS): P[pid]["extracao"]=s

# ---------------------------------------------------------------- 3. gabarito
@etapa("gabarito")
def gabarito():
    import gab_enem,gab_generico
    for pid in PIDS:
        if P[pid]["estado"]!="verde": continue
        qs=json.load(open(pasta(pid)+"/questoes.json")); g=gab_id(pid); cor=CAT[pid].get("caderno") or None
        if not g: P[pid].update(estado="vermelha",motivo="sem gabarito ligado no catálogo"); continue
        melhor=None
        for nome,le in (("gab_enem",gab_enem.le),("gab_generico",gab_generico.le)):
            try: gg=le(R+"/"+CAT[g]["caminho"],cor)
            except (SystemExit,Exception) as e: continue
            dif=[]
            for x in qs:
                k=(x["numero"],x.get("idioma")) if (x["numero"],x.get("idioma")) in gg else (x["numero"],None)
                o=gg.get(k); b="anulada" if x.get("anulada") else x.get("gabarito")
                if o is None or o!=b: dif.append((x["id"],o,b))
            if melhor is None or len(dif)<len(melhor[1]): melhor=(nome,dif,len(gg),sorted({k[0] for k in gg}))
            if not dif: break
        if not melhor: P[pid].update(estado="vermelha",motivo="gabarito oficial não lido"); continue
        P[pid]["gabarito"]={"leitor":melhor[0],"chaves":melhor[2],"conferidas":len(qs),"divergencias":melhor[1][:20]}
        # questoes que o gabarito oficial tem e o extrator nao achou: pendentes "não extraída" (a prova nao fica completa)
        P[pid]["nao_extraidas"]=sorted(set(melhor[3])-{x["numero"] for x in qs})
        # letra oficial diferente da extraida (ou oficial ausente) = numeracao/cor errada: prova VERMELHA. Ja a questao que o
        # extrator nao leu direito (sem letra, ex.: virou "discursiva" por falta de alternativas) so vira pendente
        sem_letra={o for o,ofi,ext in melhor[1] if ext is None and ofi is not None}
        P[pid]["sem_letra"]=sorted(sem_letra); graves=[x for x in melhor[1] if x[0] not in sem_letra]
        if graves: P[pid].update(estado="vermelha",motivo=f"gabarito: {len(graves)} divergência(s) entre o PDF oficial e a extração")

# ---------------------------------------------------------------- 4. casa com o banco
@etapa("casa")
def casa():
    if not A.banco: return
    def um(pid):
        if P[pid]["estado"]!="verde": return pid,None
        r=sh(["python3",EN+"/integra.py",A.banco+"/final/partes",pasta(pid),f"{TMP}/int_{pid}.json",CORRF],cwd=R)
        open(f"{TMP}/logs/integra_{pid}.log","w").write(r.stdout+r.stderr)
        if r.returncode: P[pid].update(estado="vermelha",motivo="integra.py falhou"); return pid,None
        return pid,r.stdout
    with cf.ThreadPoolExecutor(A.paralelo) as ex: list(ex.map(um,PIDS))

# ---------------------------------------------------------------- 5. separa prontas x pendentes
TIPOS=[  # (tipo, regex do alerta) — o primeiro que casar da o tipo; alerta "ajuste à mão" nao bloqueia
    ("símbolo",r"PENDENTE: há um trecho desenhado|símbolos lidos de glifos|caractere estranho"),
    ("transcrição",r"PENDENTE: o texto deste trecho|texto desenhado no PDF"),
    ("fórmula",r"é pequena \(pode ser fórmula"),
    ("tabela",r"tabela transcrita automaticamente"),
    ("figura",r"pode estar cortada|tem texto dentro|texto curto solto junto da imagem|figura na pág"),
    ("texto depois das alternativas",r"há texto depois das alternativas"),
    ("hífen",r"hífen incerto"),
    ("alternativas",r"alternativa vazia|alternativas com texto idêntico|alternativas fora|alternativas encontradas|letras fora de ordem|alternativas em tabela"),
    ("gabarito",r"sem gabarito"),
]
def tipo_alerta(a):
    if a.startswith("ajuste à mão"): return None
    for t,rx in TIPOS:
        if re.search(rx,a): return t
    return "outro"
def problemas(r):
    """motivos que impedem publicar sem olhar (lista de (tipo, texto))"""
    m=[]
    if r["origem_texto"] not in CORR:   # questao com correcao feita olhando a imagem: os alertas ja foram resolvidos
        for a in r.get("alertas",[]):
            t=tipo_alerta(a)
            if t: m.append((t,a))
    import copy; x=copy.deepcopy(r); _corr.aplica(x,CORR)
    s=json.dumps([x["statement"],x["alternativas"],x.get("apos_alternativas","")],ensure_ascii=False)
    if "(cid:" in s or re.search(r"[-]",s): m.append(("símbolo","símbolo sem tradução no texto ((cid:) ou U+E000–U+F8FF)"))
    al=x["alternativas"]
    if [a["letra"] for a in al]!=list("ABCDE"): m.append(("alternativas","alternativas fora do padrão A–E"))
    elif any(not a["texto"].strip() for a in al): m.append(("alternativas","alternativa vazia"))
    if not re.sub(r"\{\{[^}]+\}\}","",x["statement"]).strip() and not x["imagens_src"]: m.append(("enunciado","enunciado vazio"))
    if re.search(r"\n\s*\(?A\)\s.+\n\s*\(?B\)\s",x["statement"]): m.append(("alternativas","alternativas dentro do enunciado"))
    refs={int(k) for k in re.findall(r"\{\{img:(\d+)\}\}",s)}
    if refs!=set(range(1,len(x["imagens_src"])+1)): m.append(("figura","imagens desencontradas do texto"))
    if x["gabarito"] not in list("ABCDE")+["anulada"]: m.append(("gabarito","sem gabarito"))
    return m
def recorte(pid,q,dest):
    """recorte das regioes da questao (caixas por pagina) num PNG so, empilhado"""
    import cv2,numpy as np
    pdf=pdf_usado(pid); partes=[]; DPI=110; s=DPI/72
    for pg,cx in sorted((q.get("caixas") or {}).items(),key=lambda kv:int(kv[0])):
        if not cx: continue
        x0=max(0,min(b[0] for b in cx)-6); y0=max(0,min(b[1] for b in cx)-6); x1=max(b[2] for b in cx)+6; y1=max(b[3] for b in cx)+6
        base=f"{TMP}/crop_{q['id']}_{pg}"
        sh(["pdftoppm","-r",str(DPI),"-f",pg,"-l",pg,"-x",str(int(x0*s)),"-y",str(int(y0*s)),"-W",str(int((x1-x0)*s)),"-H",str(int((y1-y0)*s)),"-png","-singlefile",pdf,base])
        if os.path.exists(base+".png"): partes.append(cv2.imread(base+".png")); os.remove(base+".png")
    if not partes: return False
    w=max(p.shape[1] for p in partes)
    partes=[cv2.copyMakeBorder(p,0,4,0,w-p.shape[1],cv2.BORDER_CONSTANT,value=(255,255,255)) for p in partes]
    cv2.imwrite(dest,np.vstack(partes)); return True
@etapa("separa")
def separa():
    for f in glob.glob(PEND+"/*"): os.remove(f)   # a lista de pendentes e refeita a cada rodada
    for pid in PIDS:
        st=P[pid]; st.update(prontas=[],pendentes={},novas=0,casadas=0,do_banco_antigo=0,gab_corrigido=[])
        if st["estado"]!="verde" or not A.banco:
            if os.path.exists(pasta(pid)+"/questoes.json") and st["estado"]!="verde":
                st["pendentes"]={q["id"]:[("prova vermelha",st["motivo"])] for q in json.load(open(pasta(pid)+"/questoes.json"))}
            continue
        d=json.load(open(f"{TMP}/int_{pid}.json")); qs={q["id"]:q for q in json.load(open(pasta(pid)+"/questoes.json"))}
        regs=[(r,None) for r in d["novas"]]+[(x["registro"],x) for x in d["casadas"]]
        for r,x in regs:
            m=problemas(r)
            if r["origem_texto"] in st.get("sem_letra",[]): m.append(("gabarito","o extrator não leu a letra desta questão (o oficial tem)"))
            if x and x["sim"]<0.97 and r["origem_texto"] not in CORR.get("_casa",{}): m.append(("casamento",f"semelhança {x['sim']} com a questão {x['id_banco']} do banco"))
            if m: st["pendentes"][r["origem_texto"]]=m
            else: st["prontas"].append(r["origem_texto"])
            if x:
                st["casadas"]+=1; st["do_banco_antigo"]+=x["id_banco"]<10000
                if x["gab_banco"]!=x["gab_oficial"]: st["gab_corrigido"].append([x["id_banco"],x["gab_banco"],x["gab_oficial"]])
            else: st["novas"]+=1
        for o,m in st["pendentes"].items():
            q=qs[o]; img=f"{PEND}/{o}.png"; ok=recorte(pid,q,img)
            r=next(r for r,_ in regs if r["origem_texto"]==o)
            json.dump({"origem":o,"prova":pid,"arquivo":CAT[pid]["caminho"],"paginas":q.get("paginas"),"motivos":[{"tipo":t,"texto":a} for t,a in m],
                       "recorte":os.path.basename(img) if ok else None,"statement":r["statement"],"alternativas":r["alternativas"],
                       "apos_alternativas":r.get("apos_alternativas",""),"imagens":[os.path.relpath(i,R) for i in r["imagens_src"]],"gabarito":r["gabarito"]},
                      open(f"{PEND}/{o}.json","w"),ensure_ascii=False,indent=1)
        for n in st.get("nao_extraidas",[]):
            o=f"{pid}-Q{n:03d}"; st["pendentes"][o]=[("não extraída","o extrator não achou o cabeçalho desta questão no PDF")]
            json.dump({"origem":o,"prova":pid,"arquivo":CAT[pid]["caminho"],"paginas":None,"motivos":[{"tipo":"não extraída","texto":"o extrator não achou o cabeçalho desta questão no PDF"}],
                       "recorte":None,"statement":"","alternativas":[],"apos_alternativas":"","imagens":[],"gabarito":None},open(f"{PEND}/{o}.json","w"),ensure_ascii=False,indent=1)
        # int_*.json para o publica.py: pendentes de fora; prova_completa so com a prova inteira pronta
        d["pendentes"]=sorted(st["pendentes"]); d["prova_completa"]=not st["pendentes"]
        json.dump(d,open(f"{TMP}/int_{pid}.json","w"),ensure_ascii=False)

# ---------------------------------------------------------------- 6. classifica as novas (vizinho mais parecido)
AREA={"NATUREZA":"naturezas","HUMANAS":"humanas","MATEM":"exatas","LINGUAGENS":"linguagens"}
def limpa_txt(s): return re.sub(r"\{\{[^}]+\}\}|\\[()]|[*_#]|<[^>]+>"," ",s or "").lower()
@etapa("classifica")
def classifica():
    if not A.banco: return
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    base=[q for f in glob.glob(A.banco+"/final/partes/*.json") for q in json.load(open(f)) if q.get("subassunto_codigo")]
    txt=lambda st,al:limpa_txt(st)[-2500:]+" "+" ".join(limpa_txt(a["texto"]) for a in al)
    V=TfidfVectorizer(strip_accents="unicode",ngram_range=(1,2),min_df=2,max_df=0.5,sublinear_tf=True,max_features=400000)
    X=V.fit_transform([txt(q["statement"],q["alternativas"]) for q in base]); X=normalize(X)
    areas=[q.get("area_codigo") for q in base]
    REL["classificacao"]=cl={}
    for pid in PIDS:
        if P[pid]["estado"]!="verde": continue
        d=json.load(open(f"{TMP}/int_{pid}.json"))
        for r in d["novas"]:
            if r["origem_texto"] in d["pendentes"]: continue
            ar=next((v for k,v in AREA.items() if k in (r.get("area_prova") or "").upper()),None)
            v=normalize(V.transform([txt(r["statement"],r["alternativas"])])); sims=(X@v.T).toarray().ravel()
            if ar: sims=sims*[a==ar for a in areas]
            top=sims.argsort()[::-1][:10]; voto=collections.Counter()
            for i in top: voto[base[i]["subassunto_codigo"]]+=sims[i]
            sub,peso=voto.most_common(1)[0]; conf=round(peso/max(1e-9,sum(voto.values())),2)
            cl[r["origem_texto"]]={"subassunto":sub,"confianca":conf,"sim1":round(float(sims[top[0]]),2),"vizinho":base[top[0]]["id"],
                                   "baixa":bool(conf<0.35 or sims[top[0]]<0.25)}
    json.dump(cl,open(f"{OUTD}/classificacao.json","w"),ensure_ascii=False,indent=0)

# ---------------------------------------------------------------- 7. publica
@etapa("publica")
def publica():
    if not A.banco: return
    ints=[f"{TMP}/int_{pid}.json" for pid in PIDS if P[pid]["estado"]=="verde"]
    if not ints: return
    r=sh(["python3",EN+"/publica.py",A.banco,CORRF]+ints,cwd=R)
    open(f"{TMP}/logs/publica.log","w").write(r.stdout+r.stderr); REL["publica"]=r.stdout[-3000:]
    if r.returncode: print(r.stdout[-2000:],r.stderr[-3000:]); raise SystemExit("publica.py falhou")
    parte=A.banco+"/final/partes/banco_parte_%s.json"%os.environ.get("PARTE","28")
    cl=REL.get("classificacao",{}); linhas=[f"{q['id']} {cl[q['origem_texto']]['subassunto']}" for q in json.load(open(parte))
                                            if q.get("origem_texto") in cl and not q.get("subassunto_codigo")]
    open(f"{OUTD}/classif.txt","w").write("\n".join(linhas)+"\n")
    if linhas:
        r=sh(["python3",EN+"/grava_classif.py",parte,f"{OUTD}/classif.txt","0"],cwd=R); REL["grava_classif"]=r.stdout.strip()[:500]
        if r.returncode: print(r.stderr[-2000:]); raise SystemExit("grava_classif.py falhou")

# ---------------------------------------------------------------- 8. verifica e relatorio
@etapa("verifica")
def verifica():
    if not A.banco: return
    vp=[pid for pid in PIDS if P[pid]["estado"]=="verde"]
    if not vp: return
    r=sh(["python3",FA+"/verifica_lote.py",A.banco,f"{TMP}"]+vp,cwd=R); REL["verifica"]=r.stdout.strip(); REL["verifica_ok"]=r.returncode==0
    print(r.stdout[-3000:],r.stderr[-2000:])
def relatorio():
    REL["tempo_s"]=TEMPO; tp=collections.Counter(); tot=collections.Counter()
    for pid in PIDS:
        st=P[pid]; REL["provas"][pid]={k:v for k,v in st.items() if k!="pendentes"}
        REL["provas"][pid]["pendentes"]={o:[t for t,_ in m] for o,m in st.get("pendentes",{}).items()}
        for m in st.get("pendentes",{}).values(): tp[m[0][0]]+=1
        tot["prontas"]+=len(st.get("prontas",[])); tot["pendentes"]+=len(st.get("pendentes",{}))
        for k in ("novas","casadas","do_banco_antigo"): tot[k]+=st.get(k,0)
        tot["gab_corrigido"]+=len(st.get("gab_corrigido",[]))
    cl=REL.get("classificacao",{}); REL["totais"]=dict(tot); REL["pendentes_por_tipo"]=dict(tp.most_common())
    json.dump(REL,open(f"{OUTD}/relatorio.json","w"),ensure_ascii=False,indent=1)
    L=[f"# Fábrica v2 — lote {LOTE}","",f"Gerado por `ferramentas_nuvem/fabrica/roda_lote.py` em {time.strftime('%d/%m/%Y %H:%M')} (sem IA).","",
       "| Prova | Arquivo | Estado | Questões | Prontas | Pendentes | Novas | Já no banco (antigo) | Gabaritos corrigidos | Prova completa |","|---|---|---|---|---|---|---|---|---|---|"]
    for pid in PIDS:
        st=P[pid]; n=len(st.get("prontas",[]))+len(st.get("pendentes",{}))
        L.append(f"| {pid} | {CAT[pid]['arquivo']} | {st['estado']}{' ('+st['motivo']+')' if st['motivo'] else ''} | {n} | {len(st.get('prontas',[]))} | {len(st.get('pendentes',{}))} | {st.get('novas',0)} | {st.get('casadas',0)} ({st.get('do_banco_antigo',0)}) | {len(st.get('gab_corrigido',[]))} | {'sim' if st['estado']=='verde' and not st.get('pendentes') else 'não'} |")
    L+=["",f"**Total:** {tot['prontas']} prontas sem IA, {tot['pendentes']} pendentes, {tot['novas']} novas, {tot['casadas']} já no banco, {tot['gab_corrigido']} gabaritos corrigidos pelo oficial.","",
        "## Pendentes por tipo (o primeiro motivo de cada questão)",""]+[f"- {t}: {n}" for t,n in tp.most_common()]
    L+=["","Recortes, texto extraído e motivo de cada pendente: `_banco/pendentes/%s/`. Mutirão: `ferramentas_nuvem/fabrica/mutirao.py %s`."%(LOTE,LOTE),"",
        "## Classificação automática (vizinho mais parecido)","",f"- classificadas: {len(cl)}; confiança baixa (para confirmar): {sum(v['baixa'] for v in cl.values())}","",
        "## Tempo de cada etapa",""]+[f"- {k}: {v} s" for k,v in TEMPO.items()]
    if "verifica" in REL: L+=["","## Verificação","","```",REL["verifica"],"```"]
    open(f"{OUTD}/relatorio.md","w").write("\n".join(L)+"\n"); print("\n".join(L))

baixa(); extrai(); gabarito(); casa(); separa(); classifica(); publica(); verifica(); relatorio()
