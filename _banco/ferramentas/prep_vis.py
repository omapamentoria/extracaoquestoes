# uso: prep_vis.py PID Qnnn... -> ~/tmp_banco/vis/<PID>_<Q>_pN.png (200 dpi, area da questao) + <PID>_<Q>.txt (extracao atual)
import json,sys,glob,os,subprocess
pid=sys.argv[1]; cods=sys.argv[2:]
d=glob.glob(os.path.expanduser(f'~/mnt/BM/_banco/questoes/*/*/{pid}'))[0]
Q={x['id'].split('-',1)[1]:x for x in json.load(open(d+'/questoes.json'))}
out=os.path.expanduser('~/tmp_banco/vis')
for c in cods:
    q=Q[c]; pdf=glob.glob(os.path.expanduser('~/mnt/BM/**/'+os.path.basename(q['arquivo_origem'])),recursive=True)
    pdf=[p for p in pdf if p.endswith(q['arquivo_origem'].split('/')[-1]) and q['arquivo_origem'].split('/')[-2] in p][0]
    for pg,cx in q['caixas'].items():
        x0=min(b[0] for b in cx)-8; y0=min(b[1] for b in cx)-8; x1=max(b[2] for b in cx)+8; y1=max(b[3] for b in cx)+8
        s=200/72
        subprocess.run(['pdftoppm','-r','200','-f',pg,'-l',pg,'-singlefile','-png','-x',str(int(x0*s)),'-y',str(int(y0*s)),'-W',str(int((x1-x0)*s)),'-H',str(int((y1-y0)*s)),pdf,f'{out}/{pid}_{c}_p{pg}'],check=True)
    with open(f'{out}/{pid}_{c}.txt','w') as f:
        f.write('ENUNCIADO:\n'+q['enunciado']+'\n\nALTERNATIVAS:\n')
        for a in q['alternativas']: f.write(a['letra']+') '+a['texto']+'\n')
        f.write('\nAPOS_ALTERNATIVAS: '+str(q.get('apos_alternativas'))+'\nFONTES: '+json.dumps(q.get('fontes'),ensure_ascii=False)+'\nIMAGENS: '+json.dumps([(i['id'],i['pagina'],i['bbox'],os.path.join(d,i['arquivo'])) for i in q['imagens']])+'\nALERTAS: '+json.dumps(q['alertas'],ensure_ascii=False)+'\n')
    print(c, list(q['caixas'].keys()))
