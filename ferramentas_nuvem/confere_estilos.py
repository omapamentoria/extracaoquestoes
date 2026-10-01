# Confere os estilos feitos pelo Gemini (ramo comentarios-gemini, pasta estilos/respostas) e, com --gravar, grava
# unificacao/estilos/estilos_final.json: {"estilos": [...], "atribuicao": {id: codigo}} para o converte/Prompt 5.
# Regras em unificacao/estilos/INSTRUCOES_GEMINI.md.
# Uso: python3 ferramentas_nuvem/confere_estilos.py <pasta do ramo comentarios-gemini> [--gravar]
import json, os, sys, glob, re, collections
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(sys.argv[1], "estilos")
ind = json.load(open(os.path.join(E, "indice.json"), encoding="utf-8"))
todos, atrib, rel, cont = [], {}, [], collections.Counter()
for i in ind:
    sub = i["subassunto"]; rd = os.path.join(E, "respostas", sub)
    lf = os.path.join(rd, "lista.json")
    if not os.path.exists(lf): cont["sem resposta"] += 1; continue
    try: lista = json.load(open(lf, encoding="utf-8"))
    except Exception: rel.append(f"{sub}: lista.json inválida"); continue
    est = lista.get("estilos") or []
    cod = [e.get("codigo") for e in est]
    probs = []
    if lista.get("subassunto") != sub: probs.append("subassunto errado na lista")
    if len(set(cod)) != len(cod) or any(not re.fullmatch(re.escape(sub) + r"-E\d{1,2}", c or "") for c in cod): probs.append(f"códigos inválidos {cod}")
    if any(not (e.get("nome") or "").strip() or not (e.get("descricao") or "").strip() for e in est): probs.append("estilo sem nome ou descrição")
    n_sem_outros = len([c for c in cod if not (c or "").endswith("-E9")])
    if not (1 <= n_sem_outros <= 10): probs.append(f"{n_sem_outros} estilos")
    sub_atrib = {}
    for n in range(1, i["partes"] + 1):
        qf = os.path.join(E, "questoes", sub, f"parte_{n:02d}.json"); pf = os.path.join(rd, f"parte_{n:02d}.json")
        qs = [q["id"] for q in json.load(open(qf, encoding="utf-8"))]
        if not os.path.exists(pf): probs.append(f"parte_{n:02d} sem resposta"); continue
        try: resp = json.load(open(pf, encoding="utf-8"))
        except Exception: probs.append(f"parte_{n:02d} JSON inválido"); continue
        por = {r.get("id"): r.get("estilo") for r in resp if isinstance(r, dict)}
        falt = [q for q in qs if por.get(q) not in cod]
        if falt: probs.append(f"parte_{n:02d}: {len(falt)} questões sem estilo válido (ex.: {falt[:3]})")
        sub_atrib.update({q: por[q] for q in qs if por.get(q) in cod})
    outros = sum(1 for v in sub_atrib.values() if v.endswith("-E9"))
    if sub_atrib and outros / len(sub_atrib) > 0.12: probs.append(f"Outros com {100 * outros / len(sub_atrib):.0f}%")
    if probs: rel.append(f"{sub}: " + "; ".join(probs)); cont["com problema"] += 1; continue
    cont["ok"] += 1
    todos += [{"codigo": e["codigo"], "subassunto_codigo": sub, "nome": e["nome"].strip(), "descricao": e["descricao"].strip(), "ordem": k + 1}
              for k, e in enumerate(est)]
    atrib.update(sub_atrib)
print(dict(cont), "questões com estilo:", len(atrib)); print("\n".join(rel[:40]))
L = ["# Conferência dos estilos (Gemini)", "", f"Subassuntos: {dict(cont)}. Questões com estilo: {len(atrib)}.", "", "## Problemas", ""] + [f"* {x}" for x in rel]
open(os.path.join(R, "docs", "estilos-conferencia.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
if "--gravar" in sys.argv:
    json.dump({"estilos": todos, "atribuicao": {str(k): v for k, v in atrib.items()}},
              open(os.path.join(R, "unificacao", "estilos", "estilos_final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("gravado")
