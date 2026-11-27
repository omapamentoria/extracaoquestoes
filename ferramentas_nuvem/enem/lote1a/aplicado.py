import json,glob,sys,copy
sys.path.insert(0,'/home/user/extracaoquestoes/ferramentas_nuvem/enem'); import corr
S='/tmp/claude-0/-home-user-extracaoquestoes/25913ed7-24fd-5640-96fe-fe4eefce8668/scratchpad'
C=corr.carrega(','.join(f'/home/user/extracaoquestoes/ferramentas_nuvem/enem/correcoes/{a}.json' for a in range(2015,2020)))
def todos():
    for f in sorted(glob.glob(S+'/int_*.json')):
        if 'P7601' in f: continue
        d=json.load(open(f))
        for r in d['novas']+[x['registro'] for x in d['casadas']]:
            r=copy.deepcopy(r); corr.aplica(r,C); yield d['pid'],r
