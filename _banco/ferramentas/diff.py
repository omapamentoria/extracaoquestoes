import json,sys,difflib,os,glob
B=os.path.expanduser('~/mnt/BM/_banco/questoes')
for pid in sys.argv[1:]:
  d=glob.glob(f'{B}/*/*/{pid}')[0]
  base=json.load(open(os.path.expanduser(f'~/tmp_banco/base_{pid}.json')))
  a=base['q']; n_mud=0
  for x in json.load(open(d+'/questoes.json')):
    o=a.get(x['id'])
    if not o: print('NOVA',x['id']); continue
    n={'img':[[round(v) for v in i['bbox']] for i in x['imagens']],'txt':x['enunciado'],'alts':[al['texto'] for al in x['alternativas']],'fontes':x['fontes'],'alertas':x.get('alertas',[])}
    for k in n:
      if n[k]!=o[k]:
        n_mud+=1
        if k=='txt':
          dd=[l[:140] for l in difflib.ndiff(o[k].split('\n\n'),n[k].split('\n\n')) if l[:1] in '+-']
          print(x['id'],'TXT',dd)
        else: print(x['id'],k.upper(),str(o[k])[:250],'->',str(n[k])[:250])
  for x in json.load(open(d+'/textos_base.json')):
    o=base['t'].get(x['id'])
    if not o: print('NOVO TB',x['id']); continue
    if o['txt']!=x['texto']:
      dd=[l[:140] for l in difflib.ndiff(o['txt'].split('\n\n'),x['texto'].split('\n\n')) if l[:1] in '+-']
      print(x['id'],'TXT',dd); n_mud+=1
    if o['fontes']!=x['fontes']: print(x['id'],'FONTES',o['fontes'],'->',x['fontes']); n_mud+=1
    if o['img']!=[[round(v) for v in i['bbox']] for i in x['imagens']]: print(x['id'],'IMG mudou'); n_mud+=1
  print(pid,'mudancas:',n_mud)
