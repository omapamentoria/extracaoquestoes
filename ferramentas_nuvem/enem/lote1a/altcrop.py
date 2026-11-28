# recorta as 5 alternativas desenhadas pela posicao das letras A-E (caixas ~10pt de largura)
import json,glob,sys,subprocess,cv2,numpy as np
S=sys.argv[1]
for qid in sys.argv[2:]:
    pid=qid.split('-')[0]; D=glob.glob(f'_banco/questoes/ENEM/*/{pid}')[0]
    q=[x for x in json.load(open(D+'/questoes.json')) if x['id']==qid][0]
    pg=q['paginas'][-1]; cx=q['caixas'][str(pg)]; ims=[i['bbox'] for i in q['imagens'] if i['pagina']==pg]
    let=[c for c in cx if 8<=c[2]-c[0]<=13 and 9<=c[3]-c[1]<=14]
    let=sorted(let,key=lambda c:c[1])[-5:]
    assert len(let)==5,(qid,let)
    x0=let[0][0]; colend=308 if x0<300 else 568
    tops=[c[1] for c in let]
    bottom=max([c[3] for c in cx]+[b[3] for b in ims])
    gaps=[b-a for a,b in zip(tops,tops[1:])]
    outs=[]
    mids=[(a+b)/2+5 for a,b in zip(tops,tops[1:])]
    for k,t in enumerate(tops):
        y0=mids[k-1] if k>0 else t+5-gaps[0]/2
        y1=mids[k] if k<4 else t+5+gaps[-1]/2
        x=x0+11; r=150/72; nome=f"{D}/img/{qid.split('-',1)[1]}_alt{'ABCDE'[k]}"
        subprocess.run(['pdftoppm','-f',str(pg),'-l',str(pg),'-r','150','-x',str(int(x*r)),'-y',str(int(y0*r)),'-W',str(int((colend-x)*r)),'-H',str(int((y1-y0)*r)),'-png','-singlefile',q['arquivo_origem'],nome],check=True)
        outs.append(nome+'.png')
    ims_=[cv2.imread(o) for o in outs]; w=max(i.shape[1] for i in ims_)
    cv2.imwrite(f'{S}/crop/alt_{qid}.png',np.vstack([cv2.copyMakeBorder(i,0,6,0,w-i.shape[1],cv2.BORDER_CONSTANT,value=(0,0,255)) for i in ims_]))
    print(qid,pg,[round(t) for t in tops],round(bottom),json.dumps(outs))
