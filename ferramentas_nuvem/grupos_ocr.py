# Agrupa as provas "outras" da lista de OCR (as 159 que nao eram de texto ruim em 29/09/2026) por tipo de problema
# e mostra o que foi recuperado. Gera docs/lotes/outras_grupos.md.
import json, os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = {r["id"]: r for r in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"), encoding="utf-8"))}
outras = open(os.path.join(R, "ferramentas_nuvem", ".outras159.txt")).read().split()
resta = set(re.findall(r"^\* (P\d{4}) — ", open(os.path.join(R, "docs", "lotes", "para_ocr.md"), encoding="utf-8").read(), re.M))
extra = set(re.findall(r"P\d{4}", open(os.path.join(R, "docs", "lotes", "ocr_extra.txt")).read()))
G = [
 ("Camada de texto inútil (página sem texto, OCR embutido ruim, fonte renumerada, questão como imagem)",
  "Tratadas como texto ruim: OCR do tesseract (`ocr_pdf.py`) e extração no modo OCR, com alerta em toda questão.",
  lambda p, c: p in extra),
 ("Arquivo que não é a prova (1 página, capa, planner, só redação)",
  "Não há o que extrair: conseguir o arquivo certo.",
  lambda p, c: str(c["paginas"]) in ("1",) or re.search(r"(?i)planner|reda[çc][ãa]o|redacao", c["arquivo"])),
 ("Prova discursiva com expectativa de resposta (UEL 2ª fase por disciplina, FAMERP dia 2, UERJ discursiva)",
  "O extrator já reconhece o formato discursivo; entram com alerta (discursivas ficam para a fase delas).",
  lambda p, c: (c["vestibular"] == "UEL" and "tipo" not in c["arquivo"].lower() and "prova-" not in c["arquivo"].lower())
               or (c["vestibular"] == "FAMERP" and re.search(r"dia 02|Prova 2", c["arquivo"]))),
 ("Cabeçalho \"QUESTÃO N\" sem negrito (FATEC, UFU, simulado UNESP, ENEM digital 2020, ENEM 2006)",
  "Regra nova `questao_nb` (vence só se a sequência for maior que a dos outros estilos); \"Questão 92 - Ciências…\" vira área.",
  lambda p, c: c["vestibular"] in ("FATEC", "UFU", "UNESP") or (c["vestibular"] == "ENEM" and c["ano"] in ("2020", "2006"))),
 ("Número grande solto, com rótulo \"Questão\" (UERJ, USS, simulados UERJ, FUVEST 2022)",
  "Regra nova `grande`; dígitos separados pela fonte (\"0 1\") são juntados; o rótulo \"Questão\" sai da linha.",
  lambda p, c: c["vestibular"] in ("UERJ", "USS") or (c["vestibular"] == "FUVEST" and c["ano"] == "2022")),
 ("Número + texto na mesma linha, sem ponto (FUVEST 2010–2018, UFGD PSV, ENEM 1998–2004, UEL tipo 1, UNEMAT)",
  "Regra nova `lead`: número em negrito ou maior que o texto, seguido do texto.",
  lambda p, c: c["vestibular"] in ("FUVEST", "UFGD", "UEL", "UNEMAT") or (c["vestibular"] == "ENEM" and c["ano"] in ("1998", "1999", "2001", "2004"))),
 ("Outros", "Ver caso a caso.", lambda p, c: True),
]
por = {i: [] for i in range(len(G))}
for p in outras:
    c = CAT[p]
    i = next(i for i, g in enumerate(G) if g[2](p, c))
    por[i].append(p)
L = ["# Provas \"outras\" da lista de OCR: grupos por tipo de problema", "",
     f"159 provas que não eram de texto ruim (29/09/2026). Recuperadas agora: **{sum(1 for p in outras if p not in resta)}**; ainda na lista: **{sum(1 for p in outras if p in resta)}**.",
     "Extrator v139 (regras condicionais; regressão das 9 provas-base sem nenhuma mudança). Rodado com `python3 ferramentas_nuvem/refaz_lista.py` (e `refaz_lista.py ocr` para o 1º grupo).", ""]
for i, (nome, acao, _) in enumerate(G):
    ps = por[i]
    if not ps: continue
    ok = [p for p in ps if p not in resta]
    L += [f"## {nome}", "", f"{len(ps)} provas; recuperadas {len(ok)}. {acao}", ""]
    for p in ps:
        c = CAT[p]
        L.append(f"* {'✔' if p not in resta else '✘'} {p} — {c['vestibular']} {c['ano']} — {c['arquivo']}")
    L.append("")
open(os.path.join(R, "docs", "lotes", "outras_grupos.md"), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(l for l in L if l.startswith("##") or "provas; recuperadas" in l or "Recuperadas agora" in l))
