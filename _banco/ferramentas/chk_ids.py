import json,glob,os,re,sys
outs={}
for f,pid in [('vis/out_A.json','P1108'),('vis/out_B.json','P1108')]:
    for k,v in json.load(open(f)).items(): outs[(pid,k)]=v
for k,v in json.load(open('vis/out_C.json')).items():
    p,q=k.split(':'); outs[(p,q)]=v
for (pid,q),v in sorted(outs.items()):
    d=glob.glob(os.path.expanduser(f'~/mnt/BM/_banco/questoes/*/*/{pid}'))[0]
    cur={x['id'].split('-',1)[1]:x for x in json.load(open(d+'/questoes.json'))}[q]
    old=open(f'vis/{pid}_{q}.txt').read(); oi=json.loads(old.split('IMAGENS: ')[1].split('\n')[0])
    oldb={i[0]:[round(x) for x in i[2]] for i in oi}; curb={i['id']:[round(x) for x in i['bbox']] for i in cur['imagens']}
    used=sorted({int(x) for x in re.findall(r'\{\{img:(\d+)\}\}', json.dumps(v,ensure_ascii=False))})
    bad=[u for u in used if oldb.get(u)!=curb.get(u)]
    print(pid,q,'usa',used,'OK' if not bad else f'DIVERGE {bad} old={ {u:oldb.get(u) for u in bad} } cur={ {u:curb.get(u) for u in bad} }', '| atual:',curb)
