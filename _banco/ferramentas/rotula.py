# uso: rotula.py <pasta da prova> "0=β" "1=→" ... (acrescenta os glifos da folha em _banco/glifos_ref.json)
import json,sys,os
d=sys.argv[1]; ref_p=os.path.expanduser('~/mnt/BM/_banco/glifos_ref.json')
ref=json.load(open(ref_p)); lista=json.load(open(os.path.join(d,'revisao','glifos_desconhecidos.json')))
for arg in sys.argv[2:]:
    n,ch=arg.split('=',1); est=''
    if ch.endswith(':i') or ch.endswith(':b'): ch,est=ch[:-2],ch[-1]
    g=[x for x in lista if x['n']==int(n)][0]
    ref.append({'char':ch,'estilo':est,'H':g['H'],'W':g['W'],'bits':g['bits'],'origem':os.path.basename(d)+'#'+n})
json.dump(ref,open(ref_p,'w'),ensure_ascii=False); print(len(ref),'glifos na tabela')
