import re
def horizontal(t):
    """gabarito em tabela: linha de numeros seguida de linha de letras (alinhadas por coluna)"""
    L=t.split("\n"); g={}
    for i in range(len(L)-1):
        nums=[(m.start(),m.end(),int(m.group())) for m in re.finditer(r"\d{1,3}",L[i])]
        if len(nums)<3 or re.search(r"[A-Za-z]{2,}",L[i]): continue
        j=i+1
        while j<len(L) and not L[j].strip(): j+=1
        if j>=len(L): continue
        lets=[(m.start(),m.group()) for m in re.finditer(r"\b([A-E]|ANULADA|X|\*)\b",L[j])]
        if len(lets)<3 or re.search(r"\d",L[j]): continue
        for s,e,n in nums:
            c=(s+e)/2; best=min(lets,key=lambda x:abs(x[0]-c))
            if abs(best[0]-c)<=3: g.setdefault(n,best[1])
    return g
