# Prova escaneada (sem texto) de uma cor + a mesma prova de outra cor com texto: monta a extracao da cor escaneada
# com o TEXTO da outra cor (mesmo texto oficial do INEP; no ENEM as cores so mudam a ordem das questoes, as
# alternativas ficam iguais) e o NUMERO e o GABARITO oficial da cor escaneada.
# Uso: cor_por_texto.py <PID escaneada> <PID com texto> <mapa.json {"<numero>|<idioma>": numero_na_cor_escaneada}> <gabarito.json {"<numero>|<idioma>": letra|"anulada"}>
# O mapa foi feito pela posicao de cada questao na camada OCR (as questoes estao em ordem numerica no caderno),
# pelo cabecalho "Questao N" lido no OCR e conferido pela imagem da pagina onde havia duvida (ver docs/enem/2020.md).
import json,os,shutil,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from catalogo import CAT
R="/home/user/extracaoquestoes/_banco/questoes/ENEM/2020/"
dst,src,mapa,gab=sys.argv[1:5]
M=json.load(open(mapa)); G=json.load(open(gab)); c=CAT[dst]
if os.path.exists(R+dst): shutil.rmtree(R+dst)
os.makedirs(R+dst); shutil.copytree(R+src+"/img",R+dst+"/img")
shutil.copy(R+src+"/textos_base.json",R+dst+"/textos_base.json")
qs=json.load(open(R+src+"/questoes.json")); out=[]
for q in qs:
    idi=q.get("idioma") or ""; n=M["%d|%s"%(q["numero"],idi)]; g=G["%d|%s"%(n,idi)]
    suf={"inglês":"-ING","espanhol":"-ESP"}.get(idi,"")
    q.update(id="%s-Q%03d%s"%(dst,n,suf),prova_id=dst,numero=n,caderno=c["caderno"],arquivo_origem=c["caminho"],
             gabarito=None if g=="anulada" else g,anulada=g=="anulada",gabarito_origem=[c["gabarito_ids"]],
             texto_de="%s questão %d (caderno %s, mesmo texto oficial)"%(src,q["numero"],CAT[src]["caderno"]))
    q["alertas"]=[a for a in q.get("alertas",[]) if a!="sem gabarito"]
    out.append(q)
out.sort(key=lambda q:(q["numero"],q.get("idioma") or ""))
assert len({q["id"] for q in out})==len(out)
json.dump(out,open(R+dst+"/questoes.json","w"),ensure_ascii=False,indent=1)
print(dst,len(out),"questões; anuladas:",[q["numero"] for q in out if q["anulada"]])
