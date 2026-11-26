# Casa as questoes extraidas da cor escolhida com as que ja estao no banco (pelo texto, nao pelo numero).
# Uso: casa.py <partes_dir> <questoes.json> <ano> <dia> <edicao> <saida.json>
import json,glob,re,sys,difflib,collections
P,QJ,ANO,DIA,ED,OUT=sys.argv[1:7]
norm=lambda s:re.sub(r"\s+"," ",re.sub(r"<[^>]+>|\{\{[^}]+\}\}|[*_\\]","",s or "").lower()).strip()
def chave(stmt,alts): return norm(stmt)+" || "+" | ".join(norm(a["texto"]) for a in alts)
banco=[]
for f in sorted(glob.glob(P+"/*.json")):
    for q in json.load(open(f)):
        if q.get("vestibular")=="ENEM" and q.get("tipo_prova")!="simulado" and str(q.get("ano"))==ANO and str(q.get("dia"))==DIA and (q.get("edicao") or "")==ED:
            banco.append(q)
novas=json.load(open(QJ))
res=[];usados=set()
for x in novas:
    kx=chave(x["enunciado"],x["alternativas"]); best=(0,None)
    for q in banco:
        if q["id"] in usados: continue
        if x.get("idioma") and q.get("idioma") and x["idioma"]!=q["idioma"]: continue
        r=difflib.SequenceMatcher(None,kx,chave(q["statement"],q["alternativas"]),autojunk=False).ratio()
        if r>best[0]: best=(r,q)
    r,q=best
    if q is not None and r>=0.80:
        usados.add(q["id"])
        # alternativas na mesma ordem?
        ordem=[max("ABCDE",key=lambda L:difflib.SequenceMatcher(None,norm(a["texto"]),norm(next((b["texto"] for b in x["alternativas"] if b["letra"]==L),""))).ratio()) for a in q["alternativas"]]
        res.append({"novo":x["id"],"numero":x["numero"],"idioma":x.get("idioma"),"id_banco":q["id"],"num_banco":q["number"],"sim":round(r,3),
                    "gab_novo":"anulada" if x["anulada"] else x["gabarito"],"gab_banco":q["gabarito"],"ordem_alt":"".join(ordem)})
    else:
        res.append({"novo":x["id"],"numero":x["numero"],"idioma":x.get("idioma"),"id_banco":None,"sim":round(r,3)})
json.dump(res,open(OUT,"w"),ensure_ascii=False,indent=0)
c=[r for r in res if r["id_banco"]]
print("no banco:",len(banco),"| casadas:",len(c),"| novas:",len(res)-len(c),"| banco sem par:",len(banco)-len(c))
for r in c:
    if r["gab_novo"]!=r["gab_banco"] or r["ordem_alt"]!="ABCDE": print("ATENCAO",r)
for r in c:
    if r["sim"]<0.95: print("sim baixa",r["numero"],r["id_banco"],r["sim"])
print("banco sem par:",[ (q["id"],q["number"]) for q in banco if q["id"] not in usados])
