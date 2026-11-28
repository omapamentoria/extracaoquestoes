# Uso: fix.py <S>   (junta $S/spec/*.json)  spec: {qid: {"motivo":..., "subs":[[velho,novo],...], "alts":{"A":"..."}, "stmt_re":[[regex,novo]], "apos":"...", "extra":{...}}}
# Para TODA questao das int_*.json: tira as imagens de enfeite (barra hachurada/◇◇◇ e faixa cinza da margem) e aplica a spec.
# Grava em correcoes/<ano>.json as regras (com contexto unico, como o corr.py exige).
import json,glob,re,sys,copy,os
S=sys.argv[1]; spec={}
for f in sorted(glob.glob(S+'/spec/*.json')): spec.update(json.load(open(f)))
sys.path.insert(0,'/home/user/extracaoquestoes/ferramentas_nuvem/enem'); from catalogo import CAT
R='/home/user/extracaoquestoes/ferramentas_nuvem/enem/correcoes/'
regs={}
for f in glob.glob(S+'/int_*.json'):
    d=json.load(open(f))
    for r in d['novas']+[x['registro'] for x in d['casadas']]: regs[r['origem_texto']]=(r,d['pid'])
BB={}
for pid in {p for _,p in regs.values()}:
    D=glob.glob(f'/home/user/extracaoquestoes/_banco/questoes/ENEM/*/{pid}')[0]
    for q in json.load(open(D+'/questoes.json')):
        for i in q['imagens']: BB[os.path.join(D,i['arquivo']).replace('/home/user/extracaoquestoes/','')]=i['bbox']
def enfeite(b):
    x0,y0,x1,y1=b; w,h=x1-x0,y1-y0
    return (h<=8 and (w<50 or w>=150)) or x1<50 or x0>570
def regras(txt,pares):
    out=[]
    for velho,novo in pares:
        while velho in txt:
            i=txt.index(velho); a,b=i,i+len(velho)
            while len(re.findall(re.escape(txt[a:b]),txt))!=1: a=max(0,a-1); b=min(len(txt),b+1)
            novo_ctx=txt[a:i]+novo+txt[i+len(velho):b]
            out.append([re.escape(txt[a:b]),novo_ctx]); txt=txt[:a]+novo_ctx+txt[b:]
    return txt,out
def tira(t,k):
    for v in ("{{img:%d}}\n\n"%k,"\n\n{{img:%d}}"%k,"{{img:%d}}"%k):
        if v in t: return v
por_ano={}; n_enf=0
for qid,(r0,pid) in sorted(regs.items()):
    sp=spec.get(qid,{}); r=copy.deepcopy(r0)
    rem=sorted(set([k for k,s in enumerate(r['imagens_src'],1) if enfeite(BB[s])]+sp.get('remove',[])))
    if not sp and not rem: continue
    n_enf+=len(rem)
    c={"motivo":sp.get("motivo","")}
    if rem: c["motivo"]=(c["motivo"]+"; " if c["motivo"] else "")+"imagem de enfeite (barra hachurada/◇◇◇ ou faixa cinza da margem) retirada"
    if sp.get('cesar'):   # sequencias (cid:N) da fonte deslocada (N+29) que sobraram depois das trocas explicitas
        sys.path.insert(0,S+'/scripts'); from cesar import dec
        t0=json.dumps([r['statement'],[a['texto'] for a in r['alternativas']],r.get('apos_alternativas'),r.get('fontes')],ensure_ascii=False)
        for v,n in sp.get('subs',[]): t0=t0.replace(json.dumps(v,ensure_ascii=False)[1:-1],'')
        runs=sorted(set(re.findall(r'(?:\(cid:\d+\))+',t0)),key=len,reverse=True)
        sp=dict(sp); sp['subs']=list(sp.get('subs',[]))+[[x,dec(x)] for x in runs]
    pares=[(v,"") for k in rem for v in [tira(r['statement'],k)] if v]+[tuple(x) for x in sp.get('subs',[])]
    _tudo=json.dumps([r['statement'],[a['texto'] for a in r['alternativas']],r.get('apos_alternativas'),r.get('fontes')],ensure_ascii=False)
    for v,n in sp.get('subs',[]):
        if json.dumps(v,ensure_ascii=False)[1:-1] not in _tudo: print('!! SUB NÃO ACHADA',qid,repr(v[:60]))
    st,ss=regras(r['statement'],pares)
    for pat,novo in sp.get('stmt_re',[]):
        n=len(re.findall(pat,st)); assert n==1,(qid,pat,n); st=re.sub(pat,lambda m:novo,st); ss.append([pat,novo])
    if ss: c['statement_sub']=ss
    alts={}
    for a in r['alternativas']:
        if a['letra'] in sp.get('alts',{}): t=sp['alts'][a['letra']]
        else:
            t=a['texto']
            for k in rem:
                v=tira(t,k)
                if v: t=t.replace(v,"",1)
            for v,n in sp.get('subs',[]): t=t.replace(v,n)
        if t!=a['texto']: alts[a['letra']]=t; a['texto']=t
    if alts: c['alternativas']=alts
    apos=r.get('apos_alternativas') or ''
    if 'apos' in sp: apos=sp['apos']
    else:
        for k in rem:
            v=tira(apos,k)
            if v: apos=apos.replace(v,"",1)
    if apos!=(r.get('apos_alternativas') or ''): c['apos_alternativas']=apos.strip()
    fo=[f for f in r.get('fontes',[])]
    for v,n in sp.get('subs',[]): fo=[f.replace(v,n) for f in fo]
    if 'fontes' in sp: fo=sp['fontes']
    if fo!=r.get('fontes',[]): c['fontes']=fo
    if rem: c['remove_imagens']=rem
    c.update(sp.get('extra',{}))
    por_ano.setdefault(CAT[pid]['ano'],{})[qid]=c
    tudo=json.dumps([st,r['alternativas'],apos,fo],ensure_ascii=False)
    resto=re.findall(r'\(cid:\d+\)|[-]',tudo)
    refs={int(x) for x in re.findall(r"\{\{img:(\d+)\}\}",tudo)}; falta=set(range(1,len(r['imagens_src'])+1))-set(rem)-refs; falta=set() if 'imagens_extra' in sp.get('extra',{}) else falta
    if sp or resto or falta: print('==',qid,'regras',len(ss),'alts',list(alts),'RESTO '+str(resto[:6]) if resto else 'ok','IMG SEM REF '+str(falta) if falta else '')
for a,cs in por_ano.items():
    f=R+a+'.json'; d=json.load(open(f))
    d={k:v for k,v in d.items() if k.startswith('_')}; d.update(cs)
    json.dump(d,open(f,'w'),ensure_ascii=False,indent=1)
print('enfeites retirados',n_enf,'| questões com correção',sum(len(v) for v in por_ano.values()))
