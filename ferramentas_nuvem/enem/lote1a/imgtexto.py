import json,glob,sys,pdfplumber,re
sys.path.insert(0,'ferramentas_nuvem/enem'); from catalogo import CAT
sys.path.insert(0,sys.argv[1]+'/scripts'); from aplicado import todos
usadas={}
for pid,r in todos():
    for s in r['imagens_src']: usadas[s]=r['origem_texto']
for p in sys.argv[2:]:
    D=glob.glob(f'_banco/questoes/ENEM/*/{p}')[0]; Q=json.load(open(D+'/questoes.json'))
    pdf=pdfplumber.open(CAT[p]['caminho'])
    for q in Q:
        for i in q['imagens']:
            src=D+'/'+i['arquivo']
            if src not in usadas: continue
            x0,y0,x1,y1=i['bbox']
            if x1<=x0: continue
            pg=pdf.pages[i['pagina']-1]
            ch=[c for c in pg.chars if c['x0']>=x0-1 and c['x1']<=x1+1 and c['top']>=y0-1 and c['bottom']<=y1+1 and c['text'].strip()]
            txt=''.join(c['text'] for c in ch)
            words=re.findall(r'[A-Za-zÀ-ú]{4,}',txt)
            area=(x1-x0)*(y1-y0); carea=sum((c['x1']-c['x0'])*(c['bottom']-c['top']) for c in ch)
            if len(words)>=6 and carea/area>0.15: print(q['id'],i['id'],[round(v) for v in i['bbox']],round(carea/area,2),txt[:70])
