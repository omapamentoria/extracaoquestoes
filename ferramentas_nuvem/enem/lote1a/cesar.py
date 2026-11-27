# decodifica sequencias de (cid:N) da fonte deslocada (N+29), para conferir com a imagem
import re,sys
ESP={3:' ',109:'ã',114:'ê',129:'ü',208:'Ô',240:'²',241:'³',191:'fi',116:'í'}
def dec(t):
    def f(m):
        ns=[int(x) for x in re.findall(r'\d+',m.group(0))]
        return ''.join(ESP.get(n, chr(n+29) if 3<n<98 else '?') for n in ns).replace('-','−')
    return re.sub(r'(?:\(cid:\d+\))+',f,t)
if __name__=='__main__': print(dec(sys.stdin.read()))
