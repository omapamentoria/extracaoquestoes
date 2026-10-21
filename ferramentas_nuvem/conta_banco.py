# Conta as questoes do banco (4 repositorios, sem as provas de docs/lotes/fora_do_banco.txt) por situacao da extracao.
# Uso: python3 ferramentas_nuvem/conta_banco.py
import json,glob,os,re,collections
fora=set(re.findall(r"^(P\d{4})",open("/home/user/extracaoquestoes/docs/lotes/fora_do_banco.txt").read(),re.M))
raizes=["/home/user/extracaoquestoes/_banco/questoes","/home/user/banco-simulados/questoes","/home/user/banco-vestibulares/questoes","/home/user/banco-demais/questoes"]
C=collections.Counter(); porrepo=collections.Counter(); alertas=collections.Counter(); provas=set(); pv=collections.Counter()
LEVE=re.compile(r"imagem \d+ (tem texto dentro|é pequena|pode estar cortada)|texto curto solto|conferir se não deveria|há texto depois das alternativas|caractere estranho|transcri|conferido com a imagem|alternativas em tabela|recortadas uma por|recortadas como imagem, uma|gabarito discursivo")
for r in raizes:
    for f in glob.glob(r+"/*/*/*/questoes.json"):
        pid=f.split("/")[-2]
        if pid in fora: continue
        provas.add(pid)
        for q in json.load(open(f,encoding="utf-8")):
            C["total"]+=1; porrepo[r.split("/")[3]]+=1
            disc=q.get("formato")=="discursiva"; C["disc" if disc else "obj"]+=1
            al=q.get("alertas",[])
            ocr=any("OCR" in a for a in al); pend=any("PENDENTE" in a for a in al)
            gab=bool(q.get("gabarito_discursivo")) if disc else bool(q.get("gabarito") or q.get("anulada"))
            nalt=len(q.get("alternativas",[]))
            alt_ok= disc or nalt>=4
            graves=[a for a in al if not LEVE.search(a) and "sem gabarito" not in a]
            if ocr: k="ocr"
            elif pend: k="pendente"
            elif not gab: k="sem_gabarito"
            elif not alt_ok: k="alternativas"
            elif not al: k="ok_sem_alerta"
            elif not graves: k="ok_alerta_leve"
            else: k="alerta_grave"
            C[("disc" if disc else "obj",k)]+=1; C[k]+=1
            for a in graves: alertas[re.sub(r"\d+","N",a)[:70]]+=1
print("provas",len(provas),dict(porrepo))
for k in ["total","obj","disc","ok_sem_alerta","ok_alerta_leve","alerta_grave","alternativas","sem_gabarito","pendente","ocr"]: print(k,C[k], "| obj",C[("obj",k)],"disc",C[("disc",k)])
print(alertas.most_common(12))
