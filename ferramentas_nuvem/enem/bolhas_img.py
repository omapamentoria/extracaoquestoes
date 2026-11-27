# Letras das alternativas desenhadas como imagens embutidas (ENEM 2012 regular): acha as caixas das bolinhas e a letra
# de cada uma pela imagem (as 5 imagens se repetem; a ordem em que aparecem na 1a questao e A, B, C, D, E).
# Grava _banco/bolhas/<PID>.json ({pagina: [[x0, top, x1, bottom, letra], ...]}), lido pelo 06_extrair.py.
# Uso: bolhas_img.py <PID>
import sys,json,hashlib,collections,pdfplumber
sys.path.insert(0,__import__("os").path.dirname(__file__)); from catalogo import CAT,R
pid=sys.argv[1]; pdf=pdfplumber.open(R+"/"+CAT[pid]["caminho"])
caixas=[]; ordem=[]
for pg in pdf.pages:
    for im in sorted(pg.images,key=lambda i:(i["x0"]>pg.width/2,i["top"])):
        w=im["x1"]-im["x0"]; h=im["bottom"]-im["top"]
        if 8<w<15 and 8<h<15:
            hs=hashlib.md5(im["stream"].get_data()).hexdigest()
            caixas.append((pg.page_number,[im["x0"],im["top"],im["x1"],im["bottom"]],hs))
            if hs not in ordem: ordem.append(hs)
cont=collections.Counter(c[2] for c in caixas)
freq=[h for h in ordem if cont[h]>1]; raras=[h for h in ordem if cont[h]==1]
# as 5 que se repetem: A-E pela ordem da 1a questao; as que aparecem uma vez so (questao com bolinhas proprias): de 5 em
# 5, na ordem em que aparecem (de cima para baixo)
assert len(freq)==5 and len(raras)%5==0, ("esperava 5 imagens de letra repetidas",len(freq),len(raras))
L={h:"ABCDE"[i] for i,h in enumerate(freq)}; L.update({h:"ABCDE"[i%5] for i,h in enumerate(raras)})
out={}
for n,b,h in caixas: out.setdefault(n,[]).append(b+[L[h]])
json.dump(out,open(R+"/_banco/bolhas/%s.json"%pid,"w"))
print(pid,{L[h]:v for h,v in cont.items()})
