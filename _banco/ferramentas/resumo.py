import json,sys,glob,os,collections
B=os.path.expanduser('~/mnt/BM/_banco/questoes')
pid=sys.argv[1]; d=glob.glob(f'{B}/*/*/{pid}')[0]
q=json.load(open(d+'/questoes.json')); t=json.load(open(d+'/textos_base.json')); nl=json.load(open(d+'/textos_nao_ligados.json'))
c=collections.Counter()
for x in q:
    for a in x['alertas']: c[a[:45]]+=1
print('alertas:',c.most_common(15))
for x in t: print('TB',x['id'],x['questoes'][:4],repr(x['texto'][:90]))
for x in nl: print('NL',x['id'],repr(x['texto'][:120]))
if len(sys.argv)>2:
    for x in q:
        if x['alertas']: print(x['id'],x['alertas'])
