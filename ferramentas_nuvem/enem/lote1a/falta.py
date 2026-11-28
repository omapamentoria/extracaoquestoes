import json,glob,re,sys
S=sys.argv[1]; spec={}
for f in glob.glob(S+'/spec/*.json'): spec.update(json.load(open(f)))
out=[]
for f in sorted(glob.glob(S+'/int_*.json')):
    d=json.load(open(f))
    for r in d['novas']+[x['registro'] for x in d['casadas']]:
        t=json.dumps([r['statement'],r['alternativas'],r['apos_alternativas']],ensure_ascii=False)
        if r['origem_texto'] in spec: continue
        if any('PENDENTE' in a for a in r['alertas']) or re.search(r'\(cid:\d+\)|[-]',t): out.append(r['origem_texto'])
print(len(out)); print(' '.join(out))
