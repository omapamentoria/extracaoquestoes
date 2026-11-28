# Verificacao da fabrica v2, depois do publica.py: para cada prova, as questoes publicadas sao exatamente as prontas
# (as pendentes ficam de fora), sem repeticao, com o gabarito oficial relido do PDF, 5 alternativas, texto, classificacao
# e sem simbolo sem traducao. Prova completa (sem pendentes): tambem os campos prova_completa* em todas.
# Uso: verifica_lote.py <Banco-de-questoes> <pasta com int_<PID>.json> <PID>...
import json,glob,sys,os,re,collections
R="/home/user/extracaoquestoes"; sys.path[:0]=[R+"/ferramentas_nuvem/enem",R+"/ferramentas_nuvem/fabrica"]
from catalogo import CAT
import gab_enem,gab_generico
DEST,TMP=sys.argv[1:3]; ok=True
Q=[q for f in glob.glob(DEST+"/final/partes/*.json") for q in json.load(open(f))]
FORA=set()
for cf in glob.glob(R+"/ferramentas_nuvem/enem/correcoes/*.json")+glob.glob(R+"/ferramentas_nuvem/fabrica/correcoes/*.json"):
    FORA|=set(json.load(open(cf)).get("_fora",{}))
def oficial(pid,nums):
    c=CAT[pid]; g=R+"/"+CAT[c["gabarito_ids"].split()[0]]["caminho"]; melhor={}
    for le in (gab_enem.le,gab_generico.le):
        try: gg=le(g,c.get("caderno") or None)
        except (SystemExit,Exception): continue
        if sum(k in gg or (k[0],None) in gg for k in nums)>sum(k in melhor or (k[0],None) in melhor for k in nums): melhor=gg
    return melhor
for pid in sys.argv[3:]:
    d=json.load(open(f"{TMP}/int_{pid}.json"))
    todas={r["origem_texto"]:r for r in d["novas"]+[x["registro"] for x in d["casadas"]]}
    esperado=set(todas)-set(d.get("pendentes",[]))-FORA
    qs=[q for q in Q if (q.get("origem_texto") or "").startswith(pid+"-")]
    cont=collections.Counter(q["origem_texto"] for q in qs); pub=set(cont)
    chave=lambda r:(r["numero"],r["idioma"])
    g=oficial(pid,[chave(r) for r in todas.values()])
    def ofi(o): r=todas.get(o); return None if r is None else g.get(chave(r),g.get((r["numero"],None)))
    falta=sorted(esperado-pub); sobra=sorted(pub-esperado); rep=[o for o,n in cont.items() if n>1]
    gab=[(q["id"],q["gabarito"],ofi(q["origem_texto"])) for q in qs if q["gabarito"]!=ofi(q["origem_texto"])]
    sem5=[q["id"] for q in qs if [a["letra"] for a in q["alternativas"]]!=list("ABCDE")]
    vaz=[q["id"] for q in qs if (not q["statement"].strip() and not q.get("imagens")) or any(not a["texto"].strip() for a in q["alternativas"])]
    sub=[q["id"] for q in qs if not q.get("subassunto_codigo")]
    sim=[q["id"] for q in qs if re.search(r"\(cid:|PENDENTE|[-]",json.dumps([q["statement"],q["alternativas"],q.get("apos_alternativas","")],ensure_ascii=False))]
    comp=d.get("prova_completa",True); nomes={q.get("prova_completa") for q in qs}
    pc_ok=(len(nomes)==1 and None not in nomes and sorted(q.get("prova_completa_ordem") for q in qs)==sorted(r["numero"] for o,r in todas.items() if o in esperado)) if comp else nomes<={None,""}
    st="OK" if not (falta or sobra or rep or gab or sem5 or vaz or sub or sim) and pc_ok else "FALHA"; ok&=st=="OK"
    print(f"{st} {pid} publicadas {len(qs)}/{len(esperado)} (pendentes fora {len(d.get('pendentes',[]))}) | prova completa {'sim' if comp else 'não'} {'ok' if pc_ok else 'ERRADA'} | "
          f"faltam {falta[:5]} | sobram {sobra[:5]} | repetidas {rep[:5]} | gabarito ≠ oficial {gab[:5]} | alternativas {sem5[:5]} | vazio {vaz[:5]} | sem classificação {sub[:5]} | símbolo {sim[:5]}")
sys.exit(0 if ok else 1)
