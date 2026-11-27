import sys,re,subprocess,cv2,numpy as np,glob,json
sys.path.insert(0,'ferramentas_nuvem/enem'); from catalogo import CAT
S=sys.argv[1]; L=[l for l in open(S+'/figs.txt') if 'pág' in l]
tiles=[]
for k,l in enumerate(L):
    p,_,pg,rest=l.split(' ',3); b=[int(x) for x in re.findall(r'-?\d+',rest.split(']')[0])]
    out=f'{S}/crop/f{k}'
    subprocess.run(['pdftoppm','-f',pg,'-l',pg,'-r','50','-x',str(int(b[0]*50/72)),'-y',str(int(b[1]*50/72)),'-W',str(int((b[2]-b[0])*50/72)+1),'-H',str(int((b[3]-b[1])*50/72)+1),'-png','-singlefile',CAT[p]['caminho'],out])
    im=cv2.imread(out+'.png'); im=cv2.copyMakeBorder(im,18,4,4,4,cv2.BORDER_CONSTANT,value=(255,255,255))
    cv2.putText(im,f'{k} {p} p{pg}',(2,13),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1); tiles.append(im)
for s in range(0,len(tiles),12):
    T=tiles[s:s+12]; W=max(t.shape[1] for t in T)
    rows=[];row=[];w=0
    for t in T:
        if w+t.shape[1]>700 and row: rows.append(row);row=[];w=0
        row.append(t); w+=t.shape[1]
    rows.append(row)
    R=[]
    for r in rows:
        h=max(t.shape[0] for t in r); R.append(np.hstack([cv2.copyMakeBorder(t,0,h-t.shape[0],0,0,cv2.BORDER_CONSTANT,value=(200,200,200)) for t in r]))
    w=max(r.shape[1] for r in R); cv2.imwrite(f'{S}/crop/folha{s//12}.png',np.vstack([cv2.copyMakeBorder(r,0,0,0,w-r.shape[1],cv2.BORDER_CONSTANT,value=(200,200,200)) for r in R]))
print(len(tiles))
