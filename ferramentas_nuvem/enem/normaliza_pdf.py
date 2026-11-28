# Copia do PDF com a MediaBox levada para a origem (0,0), sem mudar o conteudo (so desloca). Usado quando a pagina
# tem MediaBox com origem fora de 0,0 (ENEM PPL 2010, 1o dia) e o extrator desalinha texto e imagem.
# Uso: normaliza_pdf.py <PID>   -> _norm/<PID>.pdf (lido pelo 06_extrair.py no lugar do original)
import sys,os
from pypdf import PdfReader,PdfWriter,Transformation
from pypdf.generic import RectangleObject
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from catalogo import CAT,R
pid=sys.argv[1]; r=PdfReader(R+"/"+CAT[pid]["caminho"]); w=PdfWriter()
for pg in r.pages:
    x0,y0,x1,y1=[float(v) for v in pg.mediabox]
    if x0 or y0: pg.add_transformation(Transformation().translate(-x0,-y0))
    box=RectangleObject([0,0,x1-x0,y1-y0])
    for k in ("/MediaBox","/CropBox","/BleedBox","/TrimBox","/ArtBox"):
        if k in pg: pg[__import__("pypdf").generic.NameObject(k)]=box
    w.add_page(pg)
os.makedirs(R+"/_norm",exist_ok=True); w.write(R+"/_norm/%s.pdf"%pid); print("ok",pid)
