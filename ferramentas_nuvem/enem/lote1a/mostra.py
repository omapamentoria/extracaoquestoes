# mostra o texto extraido de uma questao (marcando os pedacos problematicos) e gera recorte da pagina
import json,glob,sys,re,subprocess,os
S=sys.argv[1]
for qid in sys.argv[2:]:
    p=qid.split('-')[0]; d=glob.glob(f'_banco/questoes/ENEM/*/{p}')[0]
    q=[x for x in json.load(open(d+'/questoes.json')) if x['id']==qid][0]
    bases={t["id"]:t for t in json.load(open(d+"/textos_base.json"))} if os.path.exists(d+"/textos_base.json") else {}
    print('#####',qid,'gab',q['gabarito'],'pags',q['paginas'])
    d_=json.load(open(f'{S}/int_{p}.json')); r=[x for x in d_['novas']+[y['registro'] for y in d_['casadas']] if x['origem_texto']==qid][0]
    print(r['statement'])
    for a in r['alternativas']: print(a['letra'],'|',a['texto'])
    if r.get('apos_alternativas'): print('APOS|',r['apos_alternativas'])
    if any('cid' in f for f in r['fontes']): print('FONTES|',r['fontes'])
    pdf=q['arquivo_origem']
    for pg in q['paginas']:
        cx=q['caixas'].get(str(pg)) or []
        if not cx: continue
        x0=min(c[0] for c in cx)-5; y0=min(c[1] for c in cx)-5; x1=max(c[2] for c in cx)+5; y1=max(c[3] for c in cx)+5
        out=f"{S}/crop/{qid}_p{pg}"; os.makedirs(f"{S}/crop",exist_ok=True)
        subprocess.run(['pdftoppm','-f',str(pg),'-l',str(pg),'-r','110','-x',str(int(x0*110/72)),'-y',str(int(y0*110/72)),'-W',str(int((x1-x0)*110/72)),'-H',str(int((y1-y0)*110/72)),'-png','-singlefile',pdf,out])
        print('IMG',out+'.png')
