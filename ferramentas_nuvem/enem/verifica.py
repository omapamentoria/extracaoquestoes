# Garante a prova inteira: para cada prova completa do ENEM no banco, confere que estao todas as questoes (1-90 ou
# 91-180, mais as 5 do outro idioma no dia 1), sem repeticao, e que o gabarito e o oficial da cor (lido de novo do PDF).
# Uso: verifica.py <Banco-de-questoes> <pid_prova>...
import json,glob,sys,os,collections,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from gab_enem import le
R="/home/user/extracaoquestoes"; from catalogo import CAT
DEST=sys.argv[1]; ok=True
Q=[q for f in glob.glob(DEST+"/final/partes/*.json") for q in json.load(open(f))]
for pid in sys.argv[2:]:
    c=CAT[pid]; g=le(R+"/"+CAT[c["gabarito_ids"].split()[0]]["caminho"],c.get("caderno"))
    qs=[q for q in Q if (q.get("origem_texto") or "").startswith(pid+"-")]
    # dia 1 com uma lingua so (ENEM 2020 digital: caderno e gabarito oficial so com ingles, sem colunas por idioma)
    # idioma: questoes 1-5 do dia 1 (2020+) ou 91-95 do dia 2 (2010-2019); so quando o gabarito tem as duas colunas
    faixa=range(1,91) if str(c["dia"])=="1" else range(91,181)
    fi=range(faixa[0],faixa[0]+5); d1=any(k[1] and k[0] in fi for k in g)
    def chave(q): return (q["prova_completa_ordem"],q.get("idioma") if d1 and q["prova_completa_ordem"] in fi else None)
    nums=collections.Counter(chave(q) for q in qs)
    esperado={(n,None) for n in faixa if not (d1 and n in fi)}|({(n,l) for n in fi for l in ("inglês","espanhol")} if d1 else set())
    # questoes postas fora da prova completa de proposito (correcoes "_fora", com motivo): nao contam como falta
    fora=set()
    for cf in glob.glob(R+"/ferramentas_nuvem/enem/correcoes/*.json"):
        for k in json.load(open(cf)).get("_fora",{}):
            if k.startswith(pid+"-"):
                m_=re.match(r".*-Q(\d+)(?:-(ING|ESP))?$",k); fora.add((int(m_.group(1)),{"ING":"inglês","ESP":"espanhol"}.get(m_.group(2)) if d1 and int(m_.group(1)) in fi else None))
    falta=sorted(esperado-set(nums)-fora,key=str); rep=[k for k,v in nums.items() if v>1]; sobra=sorted(set(nums)-esperado,key=str)
    gab=[(k,q["gabarito"],g.get(k)) for q in qs for k in [chave(q)] if q["gabarito"]!=g.get(k)]
    sem5=[q["id"] for q in qs if len(q["alternativas"])!=5]
    vaz=[q["id"] for q in qs if not q["statement"].strip() or any(not a["texto"].strip() for a in q["alternativas"])]
    sub=[q["id"] for q in qs if not q.get("subassunto_codigo")]
    nomes={q.get("prova_completa") for q in qs}
    st="OK" if not (falta or rep or sobra or gab or sem5 or vaz or sub) and len(nomes)==1 else "FALHA"; ok&=st=="OK"
    print(f"{st} {pid} {list(nomes)} questões {len(qs)}/{len(esperado)} | fora (explicadas) {sorted(fora,key=str)} | faltam {falta} | repetidas {rep} | sobram {sobra} | gabarito ≠ oficial {gab} | sem 5 alt {sem5} | texto vazio {vaz} | sem classificação {sub} | anuladas {sum(q['gabarito']=='anulada' for q in qs)}")
sys.exit(0 if ok else 1)
