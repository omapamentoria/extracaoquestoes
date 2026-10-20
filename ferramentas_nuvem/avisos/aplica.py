# Aplica as correcoes da rodada de avisos (outubro/2026) nas partes do banco. Uso: aplica.py <av> <saida_partes> <saida_quarentena>
import json,glob,sys,re,os,collections
S,OUT,QUAR=sys.argv[1:4]
L=lambda n:json.load(open(f"{S}/{n}"))
NOTE=L("fix_note.json"); REAL=L("fix_realinha.json"); DUP=L("fix_dupletra.json"); TROC=L("fix_gab_trocado.json")
SAS=L("sas_gab.json"); SASC=L("sas_confere.json"); POLI=L("poli_gab.json")
COM={"passos_raciocinio":[],"analise_correta_titulo":"","analise_correta_texto":"","analise_incorretas_intro":"","analise_incorretas":[],"quadro_resumo":[],"leve_para_prova":"","flashcards":[]}
ROD=re.compile(r"\s*\b\d{1,2}\s+SSA\s*[-–]\s*\dª\s*FASE\s+\dº\s*DIA\b\s*|\s*\bSSA\s*[-–]\s*\dª\s*FASE\s+\dº\s*DIA\s+\d{1,2}\b\s*")
JUST_CORTA={7809,7814,7818,7826,7834,7839,7840,7841,7842}
QUAR_IDS={7807:"texto misturado com outra questão e com a justificativa",7810:"texto misturado com outra questão",
  7811:"texto misturado com a justificativa",7824:"texto misturado com a justificativa",
  7837:"justificativa da prova aponta E e o gabarito gravado é B",7864:"alternativas misturadas com outras questões",
  7931:"alternativas misturadas com outras questões",7988:"alternativas misturadas com outras questões",8042:"alternativas misturadas com outras questões",
  9728:"alternativas misturadas entre colunas",101566:"gabarito oficial (A) contradiz a resolução oficial (difração = D)"}
for i in (3165,8085,8086,8087,8116,8117,8118,8729,8784,8793,8804,8808,8810): QUAR_IDS.setdefault(i,"símbolos quebrados na extração (cid)")
for i in (101057,101080,101088,101089,101108,101121,101129,101130): QUAR_IDS.setdefault(i,"alternativas deslocadas que não deu para realinhar com segurança")
QUAR_PROVA={"P3779":"gabarito da pasta é de outro simulado","P3780":"gabarito da pasta é de outro simulado","P3783":"gabarito da pasta é de outro simulado",
  "P3787":"gabarito da pasta é de outro simulado","P3788":"gabarito da pasta é de outro simulado","P1233":"gabarito não confirmado",
  "P1692":"gabarito não confirmado (só A e B)","P3006":"gabarito não confirmado","P3014":"gabarito não confirmado"}
STOP=set("a o e de da do das dos em no na nos nas um uma que para com por se ao as os é não mais como".split())
W=lambda s:{w for w in re.findall(r"[a-zà-ú]{5,}",re.sub(r"<[^>]+>|\{\{[^}]+\}\}","",s.lower())) if w not in STOP}
PBL={}
for p,v in POLI.items():
    t=open(f"{S}/gabs/{v['g']}.txt").read(); hs=list(re.finditer(r"QUEST[ÃA]O\s+(\d{1,3})",t)); bl={}
    for i,h in enumerate(hs): bl.setdefault(int(h.group(1)),t[h.end():hs[i+1].start() if i+1<len(hs) else len(t)][:3000])
    PBL[p]=bl
# so vale o formato "Gabarito: X" nas provas em que a maioria das questoes do banco casa com o bloco do gabarito
def _casa(p):
    tot=ok=0
    for f_ in glob.glob(S+"/partes/banco_parte_*.json"):
        for q in json.load(open(f_)):
            o=q.get("origem_texto") or ""
            if o.startswith(p+"-Q"):
                tot+=1; n=int(o.split("-Q")[1][:3]); bl=PBL[p].get(n)
                wq=W(q["statement"]+" ".join(a["texto"] for a in q["alternativas"]))
                ok+=bool(bl and len(wq&W(bl))/max(1,len(wq))>=0.6)
    return tot and ok/tot>=0.5
POLI={p:v for p,v in POLI.items() if _casa(p)}
print("provas com gabarito comentado conferido:",sorted(POLI))
log=[]; quar=[]; cont=collections.Counter(); por_id={}
def novo_gab(q,g,origem):
    if g==q["gabarito"]: return
    log.append((q["id"],"gabarito",f"{q['gabarito']} → {g} ({origem}); comentário removido para refazer")); cont["gabarito corrigido"]+=1
    q["gabarito"]=g; q.update(json.loads(json.dumps(COM)))
os.makedirs(OUT,exist_ok=True)
for f in sorted(glob.glob(S+"/partes/banco_parte_*.json")):
    lista=json.load(open(f)); fica=[]
    for q in lista:
        i=q["id"]; o=q.get("origem_texto") or ""; p=o.split("-")[0]; n=int(o.split("-Q")[1][:3]) if "-Q" in o else None
        lingua="-ING" in o or "-ESP" in o
        mot=QUAR_IDS.get(i) or QUAR_PROVA.get(p)
        # SAS: gabarito so pela resolucao conferida pelo conteudo
        if not mot and p in SAS and p not in QUAR_PROVA:
            sc=SASC.get(str(i))
            if lingua or not sc or sc[1] is None or sc[1]<0.12: mot="simulado SAS: gabarito não confirmado na resolução"
            else: novo_gab(q,sc[2],"resolução SAS")
        if not mot and p in POLI and n is not None:
            bl=PBL[p].get(n); g=POLI[p]["gab"].get(str(n))
            wq=W(q["statement"]+" ".join(a["texto"] for a in q["alternativas"]))
            if bl and g and len(wq&W(bl))/max(1,len(wq))>=0.6: novo_gab(q,g,"gabarito comentado da prova")
            elif q["gabarito"]!=g: mot="gabarito não confirmado no gabarito comentado"
        if mot:
            quar.append({**q,"_motivo_quarentena":mot}); cont["quarentena"]+=1; log.append((i,"quarentena",mot)); continue
        if str(i) in TROC["fix"]:
            a,g,pp,nn=TROC["fix"][str(i)]; novo_gab(q,"anulada" if g=="anulada" else g,"gabarito oficial da própria prova")
        # texto
        if str(i) in NOTE:
            v=NOTE[str(i)]
            for a,t in zip(q["alternativas"],v["alts"]): a["texto"]=t
            q["statement"]=q["statement"].rstrip()+"\n\n"+v["nota"]; cont["note e adote"]+=1; log.append((i,"texto","Note e adote tirado das alternativas"))
        if str(i) in REAL:
            v=REAL[str(i)]; q["statement"]=v["statement"]
            for a,t in zip(q["alternativas"],v["alts"]): a["texto"]=t
            cont["alternativas realinhadas"]+=1; log.append((i,"texto","alternativas realinhadas com o PDF"))
        if str(i) in DUP:
            for a,t in zip(q["alternativas"],DUP[str(i)]): a["texto"]=t
            cont["letras duplicadas"]+=1; log.append((i,"texto","alternativas com letra repetida"))
        if i in JUST_CORTA:
            k=q["statement"].find("JUSTIFICATIVA"); q["statement"]=q["statement"][:k].rstrip(); cont["justificativa cortada"]+=1; log.append((i,"texto","justificativa tirada do enunciado"))
        t2=ROD.sub(" ",q["statement"]).strip()
        if t2!=q["statement"].strip(): q["statement"]=t2; cont["rodapé"]+=1; log.append((i,"texto","rodapé SSA tirado"))
        fica.append(q)
    json.dump(fica,open(os.path.join(OUT,os.path.basename(f)),"w",encoding="utf-8"),ensure_ascii=False,indent=0)
os.makedirs(os.path.dirname(QUAR),exist_ok=True)
json.dump(quar,open(QUAR,"w",encoding="utf-8"),ensure_ascii=False,indent=0)
json.dump(log,open(S+"/log_aplica.json","w"),ensure_ascii=False)
print(dict(cont)); print(collections.Counter(m for _,k,m in log if k=="quarentena").most_common())
