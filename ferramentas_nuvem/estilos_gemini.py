# Monta o pacote dos estilos de questao para o Gemini, no ramo comentarios-gemini do Banco-de-questoes:
#   estilos/INSTRUCOES.md (copiado de unificacao/estilos/INSTRUCOES_GEMINI.md), estilos/taxonomia.txt,
#   estilos/indice.json, estilos/exemplos/ (os 3 pilotos), estilos/questoes/<SUB>/parte_NN.json (ate 150 por parte),
#   estilos/respostas/ (vazio; o Gemini grava aqui).
# Uso: python3 ferramentas_nuvem/estilos_gemini.py <pasta do ramo comentarios-gemini>
import json, os, sys, glob, shutil
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(sys.argv[1], "estilos"); POR = 150
M = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
S = {s["codigo"]: s for s in M["subassuntos"]}; A = {a["codigo"]: a for a in M["assuntos"]}; MT = {m["codigo"]: m for m in M["materias"]}
if os.path.isdir(os.path.join(DEST, "questoes")): shutil.rmtree(os.path.join(DEST, "questoes"))
for d in ("questoes", "respostas", "exemplos"): os.makedirs(os.path.join(DEST, d), exist_ok=True)
open(os.path.join(DEST, "respostas", ".gitkeep"), "w").close()
shutil.copy(os.path.join(R, "unificacao", "estilos", "INSTRUCOES_GEMINI.md"), os.path.join(DEST, "INSTRUCOES.md"))
shutil.copy(os.path.join(R, "unificacao", "classif", "taxonomia.txt"), os.path.join(DEST, "taxonomia.txt"))
for f in glob.glob(os.path.join(R, "unificacao", "estilos", "listas", "*.json")):
    shutil.copy(f, os.path.join(DEST, "exemplos", os.path.basename(f)))
ind = []
for f in sorted(glob.glob(os.path.join(R, "unificacao", "estilos", "questoes", "A*.json"))):
    sub = os.path.basename(f)[:-5]
    if "_" in sub: continue
    qs = json.load(open(f, encoding="utf-8")); a = A[S[sub]["assunto_codigo"]]
    d = os.path.join(DEST, "questoes", sub); os.makedirs(d)
    partes = [qs[k:k + POR] for k in range(0, len(qs), POR)]
    for n, p in enumerate(partes, 1):
        json.dump(p, open(os.path.join(d, f"parte_{n:02d}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    ind.append({"subassunto": sub, "nome": S[sub]["nome"], "assunto": a["nome"], "materia": MT[a["materia_codigo"]]["nome"],
                "questoes": len(qs), "partes": len(partes)})
ind.sort(key=lambda i: (i["materia"], i["subassunto"]))
json.dump(ind, open(os.path.join(DEST, "indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(ind), "subassuntos;", sum(i["questoes"] for i in ind), "questões;", sum(i["partes"] for i in ind), "partes")
