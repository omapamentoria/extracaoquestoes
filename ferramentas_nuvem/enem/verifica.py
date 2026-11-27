# Garante a prova inteira: para cada prova completa do ENEM no banco, confere que estao todas as questoes (1-90 ou
# 91-180, mais as 5 do outro idioma no dia 1), sem repeticao, e que o gabarito e o oficial da cor (lido de novo do PDF).
# Uso: verifica.py <Banco-de-questoes> <pid_prova>...
import json,glob,sys,os,collections,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); from gab_enem import le
R="/home/user/extracaoquestoes"; from catalogo import CAT
DEST=sys.argv[1]; ok=True
Q=[q for f in glob.glob(DEST+"/final/partes/*.json") for q in json.load(open(f))]
for pid in sys.argv[2:]:
    c=CAT[pid]; g=le(R+"/"+CAT[c["gabarito_ids"].split()[0]]["caminho"])
    qs=[q for q in Q if (q.get("origem_texto") or "").startswith(pid+"-")]
    # dia 1 com uma lingua so (ENEM 2020 digital: caderno e gabarito oficial so com ingles, sem colunas por idioma)
    d1=str(c["dia"])=="1" and any(k[1] for k in g)
    nums=collections.Counter((q["prova_completa_ordem"],q.get("idioma") if q["prova_completa_ordem"]<=5 and d1 else None) for q in qs)
    faixa=range(1,91) if str(c["dia"])=="1" else range(91,181)
    esperado={(n,None) for n in faixa if not (d1 and n<=5)}|({(n,l) for n in range(1,6) for l in ("inglês","espanhol")} if d1 else set())
    falta=sorted(esperado-set(nums),key=str); rep=[k for k,v in nums.items() if v>1]; sobra=sorted(set(nums)-esperado,key=str)
    gab=[(k,q["gabarito"],g.get(k)) for q in qs for k in [(q["prova_completa_ordem"],q.get("idioma") if q["prova_completa_ordem"]<=5 and d1 else None)] if q["gabarito"]!=g.get(k)]
    sem5=[q["id"] for q in qs if len(q["alternativas"])!=5]
    vaz=[q["id"] for q in qs if not q["statement"].strip() or any(not a["texto"].strip() for a in q["alternativas"])]
    sub=[q["id"] for q in qs if not q.get("subassunto_codigo")]
    nomes={q.get("prova_completa") for q in qs}
    st="OK" if not (falta or rep or sobra or gab or sem5 or vaz or sub) and len(nomes)==1 else "FALHA"; ok&=st=="OK"
    print(f"{st} {pid} {list(nomes)} questões {len(qs)}/{len(esperado)} | faltam {falta} | repetidas {rep} | sobram {sobra} | gabarito ≠ oficial {gab} | sem 5 alt {sem5} | texto vazio {vaz} | sem classificação {sub} | anuladas {sum(q['gabarito']=='anulada' for q in qs)}")
sys.exit(0 if ok else 1)
