# Fase 5a: area de cada questao do banco unificado, sem IA:
#  1) titulo de area impresso na prova ("CIENCIAS DA NATUREZA E SUAS TECNOLOGIAS" -> naturezas);
#  (a regra pela faixa do numero no ENEM foi descartada: a ordem das areas mudou varias vezes e errou em 945 casos)
#  3) questao antiga ja classificada na plataforma: area que ela ja tem.
# Saida: unificacao/classificacao.json  {id: {"area_codigo": ..., "fonte_area": ...}}
# Uso: python3 ferramentas_nuvem/classifica_area.py <pasta do Banco-de-questoes>
import json, os, sys, glob, re, unicodedata, collections

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = sys.argv[1]
MAPA = json.load(open(os.path.join(R, "docs", "plataforma", "mapa_banco_2026-09-30.json"), encoding="utf-8"))
ja = {q["id"]: q for q in MAPA["questoes"]}
SAIDA = os.path.join(R, "unificacao", "classificacao.json")
cls = json.load(open(SAIDA)) if os.path.exists(SAIDA) else {}


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if not unicodedata.combining(c))


def area_do_titulo(t):
    t = norm(t)
    if "natureza" in t: return "naturezas"
    if "humanas" in t: return "humanas"
    if "matematica" in t: return "exatas"
    if "linguagens" in t or "codigos" in t: return "linguagens"
    return None


cont = collections.Counter()
for f in sorted(glob.glob(os.path.join(DEST, "final", "partes", "banco_parte_*.json"))):
    for q in json.load(open(f, encoding="utf-8")):
        c = cls.setdefault(str(q["id"]), {})
        if c.get("area_codigo"): cont["já tinha"] += 1; continue
        a, fonte = None, None
        if q["id"] in ja and ja[q["id"]].get("area"):
            a, fonte = ja[q["id"]]["area"], "plataforma"
        if not a and q.get("area_prova"):
            a, fonte = area_do_titulo(q["area_prova"]), "título de área da prova"
        if a:
            c["area_codigo"] = a; c["fonte_area"] = fonte; cont[fonte] += 1
        else:
            cont["sem área"] += 1
json.dump(cls, open(SAIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(dict(cont))
