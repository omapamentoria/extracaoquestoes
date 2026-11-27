# novas de cada int_*.json x todas as questoes ENEM do mesmo ano no banco (qualquer edicao/dia), exceto as ja casadas
import json,glob,re,sys,difflib
S=sys.argv[1]
norm=lambda s:re.sub(r"\W+","",re.sub(r"<[^>]+>|\{\{[^}]+\}\}|\\[()]","",s or "").lower())
ch=lambda st,al:norm(st)[-1500:]+"|"+"|".join(norm(a["texto"]) for a in al)
Q=[q for f in glob.glob('/home/user/banco-de-questoes/final/partes/*.json') for q in json.load(open(f)) if str(q.get('ano')) in ('2015','2016','2017','2018','2019') and (q.get('exam')=='ENEM' or q.get('vestibular')=='ENEM') and q.get('tipo_prova')!='simulado' and not str(q.get('edicao') or '').startswith('Simulado')]
casados={x['id_banco'] for f in glob.glob(S+'/int_*.json') for x in json.load(open(f))['casadas']}
print('banco ENEM 2015-19 não simulado:',len(Q),'casados:',len(casados))
for f in sorted(glob.glob(S+'/int_*.json')):
    d=json.load(open(f)); ano=d['pid']
    for r in d['novas']:
        kr=ch(r['statement'],r['alternativas']); g={kr[i:i+6] for i in range(0,len(kr),3)}
        best=[]
        for q in Q:
            if q['id'] in casados: continue
            kq=ch(q['statement'],q['alternativas'])
            if len(g & {kq[i:i+6] for i in range(len(kq)-5)})<0.3*len(g): continue
            best.append((round(difflib.SequenceMatcher(None,kr,kq,autojunk=False).ratio(),3),q['id'],q.get('ano'),q.get('edicao'),q.get('dia'),q.get('number'),q['gabarito']))
        if best: print(d['pid'],r['numero'],r.get('idioma'),r['gabarito'],max(best))
