import json,glob,re,collections,sys
P="P7581 P7583 P7577 P7579 P7585 P7587 P7589 P7591 P7593 P7595 P7597 P7599 P7605 P7607 P7609 P7611 P7613 P7615 P7617 P7619".split()
tipos=collections.Counter(); cids=collections.defaultdict(collections.Counter)
for p in P:
    d=glob.glob(f'_banco/questoes/ENEM/*/{p}')[0]; Q=json.load(open(d+'/questoes.json'))
    for q in Q:
        t=json.dumps([q['enunciado'],q['alternativas'],q.get('apos_alternativas')],ensure_ascii=False)
        al=[a for a in q.get('alertas',[]) if 'PENDENTE' in a or 'desenhado' in a]
        pu=re.findall(r'[-]',t); cc=re.findall(r'\(cid:\d+\)',t)
        if not (al or pu or cc): continue
        for x in cc+pu: cids[p][x]+=1
        k=[]
        for a in al:
            if 'entre' in a and 'sem texto' in a: k.append('entre')
            elif 'símbolo que o PDF' in a: k.append('cid')
            elif 'alternativas' in a and 'desenhado' in a: k.append('altimg')
            elif 'trecho precisa' in a: k.append('geral')
            else: k.append(a[:60])
        tipos.update(set(k))
        print(q['id'],collections.Counter(k).most_common(),sorted(set(cc+pu))[:6])
print(tipos)
for p,c in cids.items(): print(p,dict(c))
