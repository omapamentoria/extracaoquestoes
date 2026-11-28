# Leitor independente de gabarito oficial em tabela (qualquer instituicao), com uma coluna por cor de caderno.
# Formatos aceitos (pdftotext -layout), todos vistos no ENEM 2000-2008:
#   "Questões AMARELA BRANCA ROSA VERDE" + linhas "Q1  A  D  D  A" ou "1  B  D  B  D"
#   "Amarela  Azul  Branca  Rosa"       + linhas "1–B  1–C  1–A  1–A"
#   uma cor so                           + linhas "1 D  2 B  3 E ..." (varios pares por linha)
# Questao anulada: "*", "X", "Anulada" ou "ANULADA" no lugar da letra.
# Uso: gab_generico.py <gabarito.pdf> <questoes.json> [cor]   -> imprime divergencias (como o gab_enem.py)
import re,sys,json,subprocess
CORES=r"amarel[oa]|branc[oa]|rosa|verde|azul|cinza|laranja"
LET=r"(?:[A-E]|\*|[Aa]nulad[oa]|ANULAD[OA])"
def _v(x): return "anulada" if x=="*" or x.lower().startswith("anulad") else x
def le(pdf,cor=None):
    t=subprocess.run(["pdftotext","-layout",pdf,"-"],capture_output=True,text=True).stdout
    g={}; col=None; k=1
    for L in t.split("\n"):
        cs=[c.lower()[:4] for c in re.findall("(?i)"+CORES,L)]
        if len(cs)>=2 and not re.search(r"\d\s*[–-]?\s*[A-E]\b",L):   # cabecalho com as cores
            if not cor or cor.lower()[:4] not in cs: raise SystemExit("tabela com varias cores: informe a cor (uma de %s)"%cs)
            col=cs.index(cor.lower()[:4]); k=len(cs); continue
        # "1–B  1–C  1–A  1–A": k pares numero-letra com traco
        pr=re.findall(r"(?<!\d)(\d{1,3})\s*[–—-]\s*("+LET+r")(?![A-Za-z])",L)
        if pr:
            if col is not None and len(pr)==k: n,v=pr[col]; g.setdefault((int(n),None),_v(v))
            elif col is None: [g.setdefault((int(n),None),_v(v)) for n,v in pr]
            continue
        # "1  D   1  D   1  E   1  B": k pares numero-letra sem traco (ENEM 2008)
        pr=re.findall(r"(?<![\w.,])(\d{1,3})\s+("+LET+r")(?![\w])",L)
        if col is not None and len(pr)==k: n,v=pr[col]; g.setdefault((int(n),None),_v(v)); continue
        # "Q1  A  D  D  A" / "1  B  D  B  D": numero e k letras
        m=re.match(r"^\s*Q?\.?\s*(\d{1,3})\s+((?:"+LET+r"\s+){%d}"%(k-1)+LET+r")\s*$",L)
        if m and col is not None:
            g.setdefault((int(m.group(1)),None),_v(m.group(2).split()[col])); continue
        if col is None:   # uma cor so: varios pares "1 D  2 B" na linha
            for n,v in re.findall(r"(?<![\w.,])(\d{1,3})\s+("+LET+r")(?![\w])",L): g.setdefault((int(n),None),_v(v))
    return g
if __name__=="__main__":
    g=le(sys.argv[1],sys.argv[3] if len(sys.argv)>3 else None); q=json.load(open(sys.argv[2])); dif=0; n=0
    for x in q:
        o=g.get((x["numero"],None)); b="anulada" if x.get("anulada") else x.get("gabarito"); n+=1
        if o!=b or o is None: dif+=1; print("DIF",x["numero"],"oficial",o,"extraido",b)
    print("conferidas",n,"divergencias",dif,"chaves no gabarito",len(g))
