# figuras do PDF (fotos e desenhos vetoriais grandes) que nao ficaram dentro de nenhuma imagem extraida
import json,glob,sys,pdfplumber
sys.path.insert(0,'ferramentas_nuvem/enem'); from catalogo import CAT
P=sys.argv[1:]
def ov(a,b): 
    ix=max(0,min(a[2],b[2])-max(a[0],b[0])); iy=max(0,min(a[3],b[3])-max(a[1],b[1])); ar=(a[2]-a[0])*(a[3]-a[1]) or 1
    return ix*iy/ar
for p in P:
    D=glob.glob(f'_banco/questoes/ENEM/*/{p}')[0]; Q=json.load(open(D+'/questoes.json'))
    ims={}; qpg={}
    for q in Q:
        for i in q['imagens']: ims.setdefault(i['pagina'],[]).append(i['bbox'])
        for pg,cx in q['caixas'].items():
            for c in cx: qpg.setdefault(int(pg),[]).append((c,q['id']))
    pdf=pdfplumber.open(CAT[p]['caminho'])
    for n,page in enumerate(pdf.pages,1):
        if n not in qpg: continue
        objs=[(o['x0'],o['top'],o['x1'],o['bottom']) for o in page.images if (o['x1']-o['x0'])>40 and (o['bottom']-o['top'])>30]
        vec=[(o['x0'],o['top'],o['x1'],o['bottom']) for o in page.curves+page.lines+page.rects]
        # agrupa vetoriais proximos
        vec=[v for v in vec if v[1]>60 and v[3]<780 and not (v[3]-v[1]<9 and v[2]-v[0]>100) and not (v[2]-v[0]<3 and v[3]-v[1]>150) and not (v[2]-v[0]<30 and v[3]-v[1]<9)]
        cl=[]
        for v in sorted(vec):
            for c in cl:
                if v[0]<c[2]+8 and v[2]>c[0]-8 and v[1]<c[3]+8 and v[3]>c[1]-8: c[:]=[min(c[0],v[0]),min(c[1],v[1]),max(c[2],v[2]),max(c[3],v[3])]; break
            else: cl.append(list(v))
        objs+= [tuple(c) for c in cl if c[2]-c[0]>60 and c[3]-c[1]>40 and c[0]>50 and c[2]<575 and c[3]-c[1]<600]
        for o in objs:
            cob=sum(ov(o,b) for b in ims.get(n,[]))
            if cob<0.5:
                # questao mais proxima
                qs=[qid for c,qid in qpg[n] if c[1]<o[3]+150 and c[3]>o[1]-150 and abs((c[0]+c[2])/2-(o[0]+o[2])/2)<200]
                print(p,'pág',n,[round(v) for v in o],'coberto',round(cob,2),sorted(set(qs))[:3])
