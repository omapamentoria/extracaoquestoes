# recorta regioes da pagina (em pt) para _banco/questoes/ENEM/<ano>/<PID>/img/<Q>_manual_<n>.png
# uso: recorta.py <qid> <pagina> x0,y0,x1,y1 [x0,y0,x1,y1 ...]
import sys,glob,json,subprocess
qid,pg=sys.argv[1],sys.argv[2]; pid=qid.split('-')[0]
D=glob.glob(f'_banco/questoes/ENEM/*/{pid}')[0]; q=[x for x in json.load(open(D+'/questoes.json')) if x['id']==qid][0]
out=[]
for n,b in enumerate(sys.argv[3:],1):
    x0,y0,x1,y1=map(float,b.split(',')); r=150/72; nome=f"{D}/img/{qid.split('-',1)[1]}_manual_{n}"
    subprocess.run(['pdftoppm','-f',pg,'-l',pg,'-r','150','-x',str(int(x0*r)),'-y',str(int(y0*r)),'-W',str(int((x1-x0)*r)),'-H',str(int((y1-y0)*r)),'-png','-singlefile',q['arquivo_origem'],nome],check=True)
    out.append(nome+'.png')
print(json.dumps(out))
