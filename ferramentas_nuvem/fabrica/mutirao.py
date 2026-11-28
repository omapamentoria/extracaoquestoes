# Fabrica v2, peca 2: monta os lotes do mutirao das pendentes (para uma sessao barata, nova a cada lote).
# Cada lote tem ate ~30 pendentes do MESMO tipo (simbolo, formula, tabela, figura...), com o recorte da pagina, o texto
# extraido e o motivo, e instrucoes curtas. A sessao le o lote e grava as correcoes em
# ferramentas_nuvem/fabrica/correcoes/<lote>.json (formato do correcoes/<ano>.json do ENEM, sempre com "motivo").
# Depois: roda_lote.py de novo (publica o que ficou pronto).
# Tambem monta a lista compacta de classificacao com confianca baixa (para confirmar).
# Uso: mutirao.py <lote> [tamanho=30]
import json,glob,os,sys,collections,re
R="/home/user/extracaoquestoes"; LOTE=sys.argv[1]; TAM=int(sys.argv[2]) if len(sys.argv)>2 else 30
PD=f"{R}/_banco/pendentes/{LOTE}"; OUT=f"{PD}/mutirao"; os.makedirs(OUT,exist_ok=True)
for f in glob.glob(OUT+"/*.md"): os.remove(f)
INSTR={
 "símbolo":"Há símbolo desenhado ou sem tradução no texto. Leia o recorte e escreva o símbolo certo (fórmula em KaTeX entre \\( \\)).",
 "transcrição":"Um trecho só existe como desenho no PDF. Transcreva-o lendo o recorte, palavra por palavra.",
 "fórmula":"Uma imagem pequena no meio do texto pode ser fórmula ou símbolo. Se for, troque {{img:N}} pela fórmula em KaTeX e liste N em remove_imagens.",
 "tabela":"O extrator montou uma tabela sozinho. Compare com o recorte: corrija célula por célula (statement_sub) ou confirme que está certa.",
 "figura":"A figura pode estar cortada, ter texto dentro ou rótulo solto. Confira com o recorte; se o texto da figura já está no enunciado, nada a fazer.",
 "texto depois das alternativas":"Há texto depois da alternativa E. Se for de outra questão ou rodapé, apague (apos_alternativas: \"\").",
 "hífen":"Palavra dividida no fim da linha. Confira no recorte se o hífen é da palavra (guarda-chuva) ou só da quebra.",
 "alternativas":"As alternativas não foram separadas direito. Escreva as 5 (alternativas_lista) lendo o recorte.",
 "enunciado":"O enunciado ficou vazio. Transcreva-o lendo o recorte.",
 "gabarito":"Sem gabarito. NÃO invente: só marque _fora com o motivo se o gabarito oficial da mesma cor não traz a questão.",
 "casamento":"A questão parece com uma que já está no banco, mas não igual. Diga se é a MESMA questão (_casa) ou outra (nada a fazer).",
}
FORMATO='''Formato da resposta (um objeto JSON; junte ao `ferramentas_nuvem/fabrica/correcoes/%s.json`):
```json
{"<origem>": {"motivo": "o que foi lido no recorte", "statement_sub": [["regex que acha o trecho", "texto certo"]],
              "alt_sub": {"B": ["regex", "texto"]}, "alternativas": {"C": "texto inteiro"}, "remove_imagens": [2]},
 "_fora": {"<origem>": "motivo (só se for impossível ter certeza)"},
 "_casa": {"<origem>": [<id no banco>, "motivo"]}}
```
Regras: cópia fiel do recorte, nada inventado. Na dúvida, `_fora` com o motivo. Nunca mude o gabarito.''' % LOTE
P=[json.load(open(f)) for f in sorted(glob.glob(PD+"/*.json"))]
grupos=collections.defaultdict(list)
for p in P: grupos[p["motivos"][0]["tipo"]].append(p)
idx=[]
for tipo,L in sorted(grupos.items(),key=lambda kv:-len(kv[1])):
    for k in range(0,len(L),TAM):
        parte=L[k:k+TAM]; nome=f"{re.sub(r'\W+','_',tipo)}_{k//TAM+1:02d}.md"
        S=[f"# Mutirão {LOTE} — {tipo} ({len(parte)} questões)","",INSTR.get(tipo,"Confira com o recorte e corrija o que estiver diferente."),"",FORMATO,""]
        for p in parte:
            alts="\n".join(f"  ({a['letra']}) {a['texto'][:300]}" for a in p["alternativas"])
            S+=[f"## {p['origem']}",f"- recorte: `_banco/pendentes/{LOTE}/{p['recorte']}`" if p["recorte"] else "- recorte: (não gerado; abra o PDF na página %s)"%p["paginas"],
                "- motivos: "+"; ".join(m["texto"][:160] for m in p["motivos"]),"","```",p["statement"][-1500:],alts,"```",""]
        open(f"{OUT}/{nome}","w").write("\n".join(S)); idx.append((nome,tipo,len(parte)))
# classificacao com confianca baixa: lista compacta (fim do enunciado + alternativas) com a sugestao
cl=f"{R}/_banco/fabrica/{LOTE}/classificacao.json"
if os.path.exists(cl):
    C={o:v for o,v in json.load(open(cl)).items() if v["baixa"]}
    if C:
        S=[f"# Confirmação de classificação — {LOTE} ({len(C)} questões)","","Para cada questão, confirme o subassunto sugerido ou troque pelo certo (taxonomia `unificacao/classif/taxonomia.txt`).",
           "Resposta: arquivo com uma linha por questão, `<origem> <subassunto>`.",""]
        for o,v in sorted(C.items()):
            p=glob.glob(f"{R}/_banco/questoes/*/*/{o.split('-')[0]}/questoes.json")
            q=next((x for x in json.load(open(p[0])) if x["id"]==o),None) if p else None
            fim=re.sub(r"\s+"," ",(q or {}).get("enunciado",""))[-300:]
            alts=" | ".join(f"{a['letra']}) {re.sub(r'\s+',' ',a['texto'])[:60]}" for a in (q or {}).get("alternativas",[]))
            S.append(f"- **{o}** sugestão `{v['subassunto']}` (confiança {v['confianca']}): …{fim} || {alts}")
        open(f"{OUT}/classificacao.md","w").write("\n".join(S)+"\n"); idx.append(("classificacao.md","classificação",len(C)))
open(f"{OUT}/INDICE.md","w").write("# Lotes do mutirão — %s\n\n"%LOTE+"\n".join(f"- `{n}`: {t}, {q} questões" for n,t,q in idx)+"\n")
print("\n".join(f"{n}: {t} ({q})" for n,t,q in idx))
