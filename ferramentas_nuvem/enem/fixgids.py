# Troca nomes de glifo /gNN (índice TrueType do Arial) pelo nome do glifo nas /Differences (só fontes Arial).
# A Arial segue a ordem padrão Mac (post format 2), MENOS dois glifos que ela não tem: 'nonbreakingspace' (172,
# usa o glifo do espaço) e 'apple' (210). Por isso: n<=171 -> ordem padrão[n]; 172..208 -> [n+1]; 209..255 -> [n+2].
# Conferido no ENEM 2021 azul: Árabe, filmación, “ ”, ‘ ’, QUESTÕES, Óleo, SO4 2−, 70 × 10−3.
# Índices acima de 255 (extensões da Arial) ficam como estão: viram PENDENTE no extrator e são lidos pela imagem.
import sys,re,io,pikepdf,collections
from fontTools.cffLib import CFFFontSet
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
                    k=n if n<=171 else n+1 if n<=208 else n+2
                    if 2<n<=255: x=pikepdf.Name('/'+SGO[k])
                    else: fora[(str(obj.BaseFont),n)]+=1
            new.append(x)
        enc.Differences=pikepdf.Array(new)
        # renomeia os mesmos glifos dentro da fonte CFF embutida, para a página continuar desenhando igual
        fd=obj.get('/FontDescriptor')
        if fd is not None and '/FontFile3' in fd and fd.FontFile3.objgen not in seen:
            seen.add(fd.FontFile3.objgen)
            cff=CFFFontSet(); cff.decompile(io.BytesIO(fd.FontFile3.read_bytes()),None); top=cff[cff.fontNames[0]]
            ren={}
            for g in top.charset:
                m=re.fullmatch(r'g(\d+)',g)
                if m and 2<int(m.group(1))<=255:
                    n=int(m.group(1)); ren[g]=SGO[n if n<=171 else n+1 if n<=208 else n+2]
            if ren:
                cs=top.CharStrings; d=cs.charStrings
                top.charset=[ren.get(g,g) for g in top.charset]
                cs.charStrings={ren.get(k,k):v for k,v in d.items()}
                if hasattr(top,'Encoding') and isinstance(top.Encoding,list): top.Encoding=[ren.get(g,g) for g in top.Encoding]
                b=io.BytesIO(); cff.compile(b,type("F",(),{"recalcBBoxes":False})())
                fd.FontFile3.write(b.getvalue())
pdf.save(dst); print('fora da tabela padrão:',dict(fora))
