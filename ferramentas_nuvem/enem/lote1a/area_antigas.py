# questoes antigas casadas cuja classificacao era de outra area que a da prova: subassunto na area da prova
import json,glob,sys
B=sys.argv[1]
M=json.load(open('/home/user/extracaoquestoes/docs/plataforma/mapa_banco_2026-09-30.json'))
SUB={s["codigo"]:s for s in M["subassuntos"] if s["ativo"]}; ASS={a["codigo"]:a for a in M["assuntos"]}; MAT={m["codigo"]:m for m in M["materias"]}
novo={104619:'A080-01',3697:'A061-06',3750:'A080-01',4083:'A030-05',100882:'A063-03',100948:'A034-02',101599:'A063-03',101646:'A080-01',101653:'A019-02',2529:'A045-08',3378:'A002-01',3382:'A080-01',3477:'A080-01'}
for f in glob.glob(B+'/final/partes/*.json'):
    txt=open(f).read(); compact=txt.count('\n')<=1; L=json.loads(txt); mud=False
    for q in L:
        if q['id'] in novo:
            s=novo[q['id']]; a=ASS[SUB[s]['assunto_codigo']]; m=MAT[a['materia_codigo']]
            q.update(area_codigo=m['area_codigo'],materia_codigo=m['codigo'],assunto_codigo=a['codigo'],subassunto_codigo=s); mud=True
    if mud:
        if compact: json.dump(L,open(f,'w'),ensure_ascii=False)
        else: json.dump(L,open(f,'w'),ensure_ascii=False,indent=0)
print('áreas das antigas ajustadas:',len(novo))
