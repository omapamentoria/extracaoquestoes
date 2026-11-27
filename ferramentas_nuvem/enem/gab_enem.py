# Leitor independente do gabarito oficial do ENEM (tabela do INEP) e conferencia com a extracao.
# Uso: gab_enem.py <gabarito.pdf> <questoes.json>   -> imprime divergencias
import re,sys,json,subprocess
def le(pdf):
    t=subprocess.run(["pdftotext","-layout",pdf,"-"],capture_output=True,text=True).stdout
    g={}
    TOK=r"(\d{1,3})\s+\*?((?:[A-E]|[Aa]nulad[oa]|ANULAD[OA])(?:\s+\*?(?:[A-E]|[Aa]nulad[oa]|ANULAD[OA]))?)"
    for L in t.split("\n"):
        for m in re.finditer(TOK+r"(?=\s|$)",L):
            n=int(m.group(1)); v=m.group(2).split()
            v=["anulada" if x.lower().startswith("anulad") else x for x in v]
            if len(v)==2 and (n<=5 or 91<=n<=95): g[(n,"inglês")]=v[0]; g[(n,"espanhol")]=v[1]   # idioma: 1-5 (2017+) ou 91-95 (2009-2016)
            elif len(v)==1: g.setdefault((n,None),v[0])
            elif len(v)==2: g.setdefault((n,None),v[0])
    return g
if __name__=="__main__":
    g=le(sys.argv[1]); q=json.load(open(sys.argv[2])); dif=0; n=0
    for x in q:
        k=(x["numero"],x.get("idioma")) if (x["numero"],x.get("idioma")) in g else (x["numero"],None)
        o=g.get(k); b="anulada" if x.get("anulada") else x.get("gabarito")
        n+=1
        if o!=b: dif+=1; print("DIF",k,"oficial",o,"extraido",b)
    print("conferidas",n,"divergencias",dif,"chaves no gabarito",len(g))
