# Leitor independente do gabarito oficial do ENEM (tabela do INEP) e conferencia com a extracao.
# Uso: gab_enem.py <gabarito.pdf> <questoes.json> [cor]   -> imprime divergencias
# Tabela com uma coluna por cor ("Gab_Azul  Gab_Amarelo ...", ENEM 2009): com [cor], so vale a coluna dessa cor.
# Idioma: pares ingles/espanhol nas questoes 1-5 (2020+) ou 91-95 (2010-2019, dia 2).
import re,sys,json,subprocess
def le(pdf,cor=None):
    t=subprocess.run(["pdftotext","-layout",pdf,"-"],capture_output=True,text=True).stdout
    g={}
    cols=None
    TOK=r"(\d{1,3})\s+\*?((?:[A-E]|[Aa]nulad[oa]|ANULAD[OA])(?:\s+\*?(?:[A-E]|[Aa]nulad[oa]|ANULAD[OA]))?)"
    for L in t.split("\n"):
        cs=[c.lower()[:4] for c in re.findall(r"(?i)gab_(azul|amarel[oa]|branc[oa]|rosa|cinza|verde)",L)]
        if len(cs)>=2:
            if not cor or cor.lower()[:4] not in cs: raise SystemExit("tabela com varias cores: informe a cor (uma de %s)"%cs)
            cols=(cs.index(cor.lower()[:4]),len(cs)); continue
        if cols:
            pr=re.findall(r"(?<![\w,])(\d{1,3})\s+([A-E]|[Aa]nulad[oa]|ANULAD[OA])(?![A-Za-z])",L)
            if len(pr)==cols[1]:
                n,v=pr[cols[0]]; g.setdefault((int(n),None),"anulada" if v.lower().startswith("anulad") else v)
            continue
        for m in re.finditer(TOK+r"(?=\s|$)",L):
            n=int(m.group(1)); v=m.group(2).split()
            v=["anulada" if x.lower().startswith("anulad") else x for x in v]
            if len(v)==2 and (n<=5 or 91<=n<=95): g[(n,"inglês")]=v[0]; g[(n,"espanhol")]=v[1]   # idioma: 1-5 (2017+) ou 91-95 (2009-2016)
            elif len(v)==1: g.setdefault((n,None),v[0])
            elif len(v)==2: g.setdefault((n,None),v[0])
    if not cols: pos(pdf,g)
    return g
def pos(pdf,g):
    # reforco por posicao na pagina (celula da letra um pouco acima/abaixo do numero, que o -layout poe em outra
    # linha): so preenche numero que a leitura por linha nao achou
    import pdfplumber
    with pdfplumber.open(pdf) as P:
        for pg in P.pages:
            ws=pg.extract_words(); L=[w for w in ws if re.fullmatch(r"[A-E]|[Aa]nulad[oa]|ANULAD[OA]",w["text"])]
            for w in ws:
                if not re.fullmatch(r"\d{1,3}",w["text"]): continue
                n=int(w["text"]); yc=(w["top"]+w["bottom"])/2; h=w["bottom"]-w["top"]
                if (n,None) in g or (n,"inglês") in g: continue
                c=sorted([x for x in L if abs((x["top"]+x["bottom"])/2-yc)<0.6*h and 0<x["x0"]-w["x1"]<130],key=lambda x:x["x0"])
                v=["anulada" if x["text"].lower().startswith("anulad") else x["text"] for x in c]
                if len(v)==2 and (n<=5 or 91<=n<=95): g[(n,"inglês")]=v[0]; g[(n,"espanhol")]=v[1]
                elif len(v)==1: g[(n,None)]=v[0]
if __name__=="__main__":
    g=le(sys.argv[1],sys.argv[3] if len(sys.argv)>3 else None); q=json.load(open(sys.argv[2])); dif=0; n=0
    for x in q:
        k=(x["numero"],x.get("idioma")) if (x["numero"],x.get("idioma")) in g else (x["numero"],None)
        o=g.get(k); b="anulada" if x.get("anulada") else x.get("gabarito")
        n+=1
        if o!=b or o is None: dif+=1; print("DIF",k,"oficial",o,"extraido",b)
    print("conferidas",n,"divergencias",dif,"chaves no gabarito",len(g))
