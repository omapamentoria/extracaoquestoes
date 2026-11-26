# Palavras grudadas (PDF justificado sem o caractere de espaco): recoloca os espacos copiando do pdftotext, que os
# reconstroi pela posicao das letras. So insere espacos: as letras ficam exatamente as mesmas, e so troca quando o
# trecho aparece no PDF de um jeito so.
import re,subprocess,collections
class Espacos:
    def __init__(self,pdf):
        t=subprocess.run(["pdftotext",pdf,"-"],capture_output=True,text=True).stdout
        t=re.sub(r"-\n(?=[a-zà-ú])","",t)            # hifenizacao de fim de linha
        t=re.sub(r"\s+"," ",t)
        self.comp=[];self.pos=[]
        for i,ch in enumerate(t):
            if ch!=" ": self.comp.append(ch); self.pos.append(i)
        self.comp="".join(self.comp); self.t=t
    def espaçado(self,tok):
        achados=set(); i=self.comp.find(tok)
        while i>=0 and len(achados)<3:
            a=self.pos[i]; b=self.pos[i+len(tok)-1]+1; achados.add(self.t[a:b]); i=self.comp.find(tok,i+1)
        return achados.pop() if len(achados)==1 else None
    def corrige(self,texto,minimo=14):
        n=0
        def tr(m):
            nonlocal n
            tok=m.group(0); core=re.sub(r"[*_]","",tok)
            if "*" in tok or "_" in tok: return tok         # trecho com marcacao: deixa para revisao
            sp=self.espaçado(core)
            if sp and " " in sp and sp.replace(" ","")==core: n+=1; return sp
            return tok
        out=re.sub(r"(?<![\\{\w])[^\s{}\\]{%d,}"%minimo,lambda m:tr(m) if re.search(r"[a-zà-ú]{3}[A-Za-zÀ-ú]*[a-zà-ú]{3}",m.group(0)) else m.group(0),texto)
        return out,n
def grudadas(texto): return re.findall(r"[A-Za-zÀ-ÿ]{22,}",texto)
