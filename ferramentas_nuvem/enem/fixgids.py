# Troca nomes de glifo /gNN (índice TrueType do Arial) pelo nome padrão Mac (post format 2) nas /Differences.
import sys,re,pikepdf,collections
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder as SGO
src,dst=sys.argv[1],sys.argv[2]
pdf=pikepdf.open(src); seen=set(); fora=collections.Counter()
for obj in pdf.objects:
    if isinstance(obj,pikepdf.Dictionary) and obj.get('/Type')=='/Font' and '/Encoding' in obj:
        enc=obj.Encoding
        if not isinstance(enc,pikepdf.Dictionary) or '/Differences' not in enc: continue
        if 'Arial' not in str(obj.BaseFont): continue  # só Arial segue a ordem padrão Mac de glifos
        if enc.objgen in seen and enc.objgen!=(0,0): continue
        seen.add(enc.objgen); new=[]
        for x in enc.Differences:
            if isinstance(x,pikepdf.Name):
                m=re.fullmatch(r'/g(\d+)',str(x))
                if m:
                    n=int(m.group(1))
                    if n<len(SGO) and n>2: x=pikepdf.Name('/'+SGO[n])
                    else: fora[(str(obj.BaseFont),n)]+=1
            new.append(x)
        enc.Differences=pikepdf.Array(new)
pdf.save(dst); print('fora da tabela padrão:',dict(fora))
