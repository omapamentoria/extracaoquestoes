# Grava a classificacao (arquivo "id_curto subassunto" ou "id subassunto") nas questoes novas da parte indicada.
# Uso: grava_classif.py <parte.json> <classif.txt> <base_id>
import json,sys
R="/home/user/extracaoquestoes"
M=json.load(open(R+"/docs/plataforma/mapa_banco_2026-09-30.json"))
SUB={s["codigo"]:s for s in M["subassuntos"] if s["ativo"]}; ASS={a["codigo"]:a for a in M["assuntos"]}; MAT={m["codigo"]:m for m in M["materias"]}
f,cf,base=sys.argv[1],sys.argv[2],int(sys.argv[3])
cl={}
for l in open(cf):
    if l.strip(): i,s=l.split(); i=int(i); cl[i if i>=base else base+i]=s
L=json.load(open(f)); n=0; area_mudou=[]
for q in L:
    s=cl.get(q["id"])
    if not s: continue
    assert s in SUB,(q["id"],s)
    a=ASS[SUB[s]["assunto_codigo"]]; m=MAT[a["materia_codigo"]]
    if q.get("area_codigo") and q["area_codigo"]!=m["area_codigo"]: area_mudou.append((q["id"],q["area_codigo"],m["area_codigo"]))
    q.update({"area_codigo":m["area_codigo"],"materia_codigo":m["codigo"],"assunto_codigo":a["codigo"],"subassunto_codigo":s}); n+=1
json.dump(L,open(f,"w"),ensure_ascii=False)
print("classificadas",n,"de",len(L),"| sem:",[q["id"] for q in L if not q.get("subassunto_codigo")][:10],"| área diferente da prova:",area_mudou)
