# uso: pacote.py <pasta_saida> PID... -> monta a pagina de revisao (index.html do rev1 + dados.json + imagens web)
import json,sys,os,glob,shutil,cv2
out=sys.argv[1]; pids=sys.argv[2:]
os.makedirs(out,exist_ok=True)
B=os.path.expanduser('~/mnt/BM/_banco'); C={d['id']:d for d in json.load(open(B+'/catalogo_debug.json',encoding='utf-8'))}
def web(src,nome,maxw=900,q=82):
    im=cv2.imread(src)
    if im is None: return None
    if im.shape[1]>maxw: im=cv2.resize(im,(maxw,int(im.shape[0]*maxw/im.shape[1])),interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(out,nome),im,[cv2.IMWRITE_JPEG_QUALITY,q]); return nome
provas=[]
for pid in pids:
    d=glob.glob(f'{B}/questoes/*/*/{pid}')[0]; P=C[pid]
    q=json.load(open(d+'/questoes.json')); t=json.load(open(d+'/textos_base.json')); nl=json.load(open(d+'/textos_nao_ligados.json'))
    for x in q+t:
        for im in x['imagens']:
            im['web']=web(os.path.join(d,im['arquivo']),f"{pid}_{os.path.basename(im['arquivo']).rsplit('.',1)[0]}.jpg")
        x['recortes_web']=[web(os.path.join(d,r),f"{pid}_{os.path.basename(r).rsplit('.',1)[0]}.jpg",maxw=700,q=70) for r in x.get('recortes',[])]
    tit=f"{P['vestibular']} {P['ano']} — {P.get('instituicao') or ''} {P.get('edicao') or ''} {P.get('fase_etapa') or ''} {('dia '+P['dia']) if P.get('dia') else ''}".replace('  ',' ')
    provas.append({'id':pid,'titulo':tit,'arquivo':P['arquivo'],'questoes':q,'textos_base':t,'nao_ligados':nl})
json.dump({'provas':provas},open(os.path.join(out,'dados.json'),'w'),ensure_ascii=False)
shutil.copy(os.path.join(B,'ferramentas','index_rev3.html'),os.path.join(out,'index.html'))
fs=os.listdir(out); print(len(fs),'arquivos', round(sum(os.path.getsize(os.path.join(out,f)) for f in fs)/1e6,1),'MB')
