import json,sys,os,glob
# uso: snap.py PID... -> salva base de cada prova
B=os.path.expanduser('~/mnt/BM/_banco/questoes')
for pid in sys.argv[1:]:
  d=glob.glob(f'{B}/*/*/{pid}')[0]
  q=json.load(open(d+'/questoes.json'))
  t=json.load(open(d+'/textos_base.json'))
  json.dump({'q':{x['id']:{'img':[[round(v) for v in i['bbox']] for i in x['imagens']],'txt':x['enunciado'],'alts':[a['texto'] for a in x['alternativas']],'fontes':x['fontes'],'alertas':x.get('alertas',[])} for x in q},
             't':{x['id']:{'txt':x['texto'],'fontes':x['fontes'],'img':[[round(v) for v in i['bbox']] for i in x['imagens']]} for x in t}},
            open(os.path.expanduser(f'~/tmp_banco/base_{pid}.json'),'w'))
  print(pid,'ok',len(q),'questoes')
