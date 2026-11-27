# Fábrica, etapa 1b: monta o catálogo do Drive novo a partir das medidas (analisa_drive2.py), sem IA.
# Separa prova / gabarito / resolução, liga prova ao gabarito (pasta, nome e número de questões),
# marca repetidos e dá a cor de triagem. Grava um arquivo por instituição em _banco/catalogo_drive2/.
# Uso: python3 monta_catalogo.py <medidas.jsonl> <pasta_textos> [ID_INICIAL=6000]
import json, os, re, sys, glob, gzip, unicodedata, collections, difflib

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(R, "_banco", "catalogo_drive2")
med = [json.loads(L) for L in open(sys.argv[1])]
TXT = sys.argv[2]
ID0 = int(sys.argv[3]) if len(sys.argv) > 3 else 6000
INI = re.compile(r"^\s*(?:QUEST[ÃA]O\s*[-–:]?\s*)?0*(\d{1,3})\s*(?:[\.\)\-–:]|$|\s)", re.M | re.I)
_cache = {}
def numeros_prova(r):
    """números que aparecem como início de questão no texto da prova"""
    if r["gid"] not in _cache:
        f = os.path.join(TXT, r["gid"] + ".txt.gz"); s = set()
        if os.path.exists(f):
            s = {int(x) for x in INI.findall(gzip.open(f, "rt").read()) if 0 < int(x) <= 300}
        _cache[r["gid"]] = s
    return _cache[r["gid"]]

def sa(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

# ---------- o que já está catalogado (Drive antigo e ENEM 2020-2025 do Drive novo)
antigo_md5 = {}; drive2_cam = {}; drive2_md5 = {}
for d in json.load(open(os.path.join(R, "_banco", "catalogo_debug.json"))):
    if d.get("md5"): antigo_md5.setdefault(d["md5"], d["id"])
    if d.get("origem") == "DRIVE2": drive2_cam[d["caminho"]] = d["id"]
for f in glob.glob(os.path.join(OUT, "*.json")):
    if re.fullmatch(r"\d{4}\.json", os.path.basename(f)):
        for d in json.load(open(f)):
            drive2_cam[d["caminho"]] = d["id"]
            if d.get("md5"): drive2_md5[d["md5"]] = d["id"]

# ---------- papel pelo nome (regras do 02_classificar.py, ampliadas)
def papel_nome(nome, pasta):
    n = sa(nome); p = sa(pasta)
    if re.search(r"folha de reda|cartao[- ]resp|modelo gab|modelo folha|errata|edital|manual|instruc|calendario|relatorio|"
                 r"matriz de ref|guia do|conteudo program|programa de|lista de obras", n): return "auxiliar"
    if re.search(r"\((com|sem)\s+gabarito\)|com gabarito", n): return "prova"
    if re.search(r"redac", n) and not re.search(r"gab|objetiv|prova [i1]\b|testes?\b", n): return "redacao"
    if re.search(r"criterio|grade de correcao|expectativa|padrao de resposta|padroes de resposta|respostas? esperadas?|"
                 r"chave de corre", n): return "padrao_resposta"
    if re.search(r"resolu|coment|correcao|^res[_ ]|_res_|cmtd|solucao|solucoes|resolvid", n): return "resolucao"
    if re.search(r"respost", n) and re.search(r"discursiv|2\s*[aª]?\s*fase|segunda fase", p + " " + n): return "padrao_resposta"
    if re.search(r"gab|(^|[_\W])gb[_\W]|respostas", n): return "gabarito"
    if re.search(r"(^|/)(gabaritos?)(/|$)", p): return "gabarito"
    if re.search(r"(^|/)(resolu[a-z]*|coment[a-z]*)(/|$)", p): return "resolucao"
    return "prova"

def faixa(x):  # [ini, fim, achados, distintos] -> (ini, fim, achados)
    return tuple(x[:3]) if x else (0, 0, 0)

def qtd_questoes(m):
    best = (0, 0, 0)
    for k in ("q_quest", "q_num", "q_esp"):
        f = faixa(m.get(k))
        if f[2] > best[2]: best = f
    return best

def faixa_de(nums):
    s = sorted(set(nums)); best = (0, 0, 0)
    for i in range(len(s)):
        for j in range(len(s) - 1, i - 1, -1):
            c = j - i + 1
            if c <= best[2]: break
            if c >= 0.8 * (s[j] - s[i] + 1): best = (s[i], s[j], c); break
    return best

TAB = re.compile(r"((?:\b\d{1,3}\s+){5,40})((?:\b(?:[A-E]|X|\*|ANULADA|Anulada|NULA)\s+){5,40})")
def tabela_texto(m):
    """linha de números seguida de linha de letras, no texto corrido (formato UFJF e outros)"""
    f = os.path.join(TXT, m["gid"] + ".txt.gz")
    if not os.path.exists(f): return (0, 0, 0)
    t = re.sub(r"\s+", " ", gzip.open(f, "rt").read()) + " "; nums = []
    for a, b in TAB.findall(t):
        na = [int(x) for x in a.split()]; lb = b.split()
        if all(y == x + 1 for x, y in zip(na, na[1:])) and len(lb) >= len(na):
            nums += na
    return faixa_de(n for n in nums if 0 < n <= 300)

def qtd_gabarito(m):
    op = [faixa(m.get("g_cob")), faixa(m.get("g_tab"))]
    if m.get("tipo") == "pdf" and (m.get("paginas") or 0) <= 6: op.append(tabela_texto(m))
    return max(op, key=lambda x: x[2])

ANO = re.compile(r"(?<!\d)(19[89]\d|20[0-2]\d)(?!\d)")
CORES = ["azul", "amarel", "branc", "rosa", "cinza", "verde", "laranja", "roxo"]

def chaves(nome):
    n = re.sub(r"[_\-.]+", " ", sa(nome))
    dia = re.search(r"(?:dia|d)\s*0?([12])\b|\b([12])\s*[ºo°]?\s*(?:dia|d)\b", n)
    fase = re.search(r"([123])\s*[ªaº°o]?\s*(?:fase|etapa|f)\b|(?:fase|etapa)\s*0?([123])", n)
    mod = re.search(r"(?:pism|modulo|serie|ano)\s*(iii|ii|i|[1-3])\b", n)
    cor = next((c for c in CORES if c in n), "")
    ver = re.search(r"versao\s*0?(\d)|\bv\s*([1-4])\b|tipo\s*([a-d1-4])\b|caderno\s*0?(\d)\b|modelo\s*([a-d1-4])\b", n)
    return {"dia": (dia.group(1) or dia.group(2)) if dia else "", "fase": (fase.group(1) or fase.group(2)) if fase else "",
            "mod": {"i": "1", "ii": "2", "iii": "3"}.get(mod.group(1), mod.group(1)) if mod else "", "cor": cor, "versao": next(x for x in ver.groups() if x) if ver else "", "ano": (ANO.findall(n) or [""])[0]}

def base_nome(nome):
    n = sa(os.path.splitext(nome)[0])
    n = re.sub(r"\(?\b(gabaritos?|gab|gb|resolucao|resolu\w*|comentad\w*|respostas?|oficial|definitivo|preliminar|"
               r"prova|caderno|cad|questoes|enunciados?)\b\)?", " ", n)
    return re.sub(r"[^a-z0-9]+", " ", n).strip()

# ---------- monta registros
regs = []
for m in med:
    partes = m["path"].split("/")
    nome = partes[-1]; pasta = "/".join(partes[:-1])
    r = dict(m)
    r["nome"], r["pasta"] = nome, pasta
    r["topo"] = partes[0] if len(partes) > 1 else ""
    r["inst"] = partes[1] if len(partes) > 2 else (partes[0] if len(partes) > 1 else "(raiz)")
    if m.get("erro") or m.get("tipo") != "pdf":
        r["papel"] = "nao_pdf" if not m.get("erro") else "erro"
    else:
        r["papel"] = papel_nome(nome, pasta)
        # conteúdo corrige o nome: arquivo curto cheio de "N letra" e sem enunciados é gabarito
        g = qtd_gabarito(m); q = qtd_questoes(m); pg = m.get("paginas", 0)
        if r["papel"] == "prova" and pg <= 3 and g[2] >= 10 and q[2] < g[2] * 0.5:
            r["papel"] = "gabarito"; r["papel_obs"] = "pelo conteúdo"
    regs.append(r)

# ---------- repetidos
por_md5 = collections.defaultdict(list)
for r in regs:
    if r.get("md5"): por_md5[r["md5"]].append(r)
for lst in por_md5.values():
    lst.sort(key=lambda r: (r["papel"] != "prova", len(r["path"]), r["path"]))
    for r in lst[1:]: r["duplicata_de_gid"] = lst[0]["gid"]

# ---------- medidas de texto
for r in regs:
    if r["papel"] in ("nao_pdf", "erro"): continue
    cp = r.get("chars_pag") or [0]; pg = max(1, r.get("paginas") or len(cp))
    sem = sum(1 for c in cp if c < 80)
    r["pag_sem_texto"] = sem; r["frac_sem_texto"] = round(sem / pg, 2)
    r["escaneado"] = r["frac_sem_texto"] >= 0.5
    r["q"] = qtd_questoes(r); r["g"] = qtd_gabarito(r)

# ---------- liga prova -> gabarito / resolução (mesma pasta ou pasta irmã/filha)
def candidatos(p, papel):
    out = []
    for r in regs:
        if r["papel"] != papel or r.get("duplicata_de_gid"): continue
        if r["pasta"] == p["pasta"]: rel = 0
        elif r["pasta"].startswith(p["pasta"] + "/"): rel = 1
        elif os.path.dirname(r["pasta"]) == os.path.dirname(p["pasta"]) and r["pasta"] != p["pasta"]: rel = 2
        elif p["pasta"].startswith(r["pasta"] + "/"): rel = 2
        else: continue
        ap, ar = ANO.findall(p["path"]), ANO.findall(r["path"])
        if ap and ar and ap[-1] != ar[-1]: continue      # ano diferente: nunca liga
        out.append((rel, r))
    return out

por_pasta_papel = collections.defaultdict(list)
for r in regs: por_pasta_papel[(r["pasta"], r["papel"])].append(r)

def pontua(p, g, rel):
    kp, kg = chaves(p["nome"]), chaves(g["nome"])
    s = 3 - rel
    for k in ("dia", "fase", "mod", "cor", "versao", "ano"):
        if kp[k] and kg[k]:
            if kp[k] == kg[k]: s += 2
            else: return -99, "não"       # dia/fase/módulo/cor/versão diferentes: nunca liga
    s += 4 * difflib.SequenceMatcher(None, base_nome(p["nome"]), base_nome(g["nome"])).ratio()
    # conteúdo: cada número do gabarito tem que aparecer como início de questão na prova
    gg = g.get("g", (0, 0, 0)); bate = "?"
    if gg[2] >= 5:
        P = numeros_prova(p); faixa_g = range(gg[0], gg[1] + 1)
        cov = sum(1 for n in faixa_g if n in P) / len(faixa_g)
        kq = faixa(p.get("q_quest"))   # "QUESTÃO N": se existe, a prova não pode ir além do gabarito
        if cov >= 0.9 and not (kq[2] >= 5 and (kq[1] > gg[1] + 1 or kq[0] < gg[0] - 1)):
            bate = "sim"; s += 5
        elif (kq[2] >= 5 and kq[0] >= gg[0] and kq[1] <= gg[1]) or \
             ((fp := faixa_de(P))[2] >= 5 and fp[0] >= gg[0] and fp[1] <= gg[1] and fp[1] - fp[0] < gg[1] - gg[0]):
            bate = "contém"; s += 1    # gabarito de vários dias/cadernos/matérias juntos
        elif cov >= 0.9:
            bate = "não"; s -= 1       # prova tem mais questões que o gabarito
        else:
            bate = "não"; s -= 3
        p.setdefault("_cov", {})[g["gid"]] = round(cov, 2)
    return s, bate

DISC = re.compile(r"discursiv|dissertativ|questoes abertas|analitico-discursiv|resposta construida")
for r in regs:
    if r["papel"] == "prova":
        r["discursiva"] = bool(DISC.search(sa(r["path"])))
provas = [r for r in regs if r["papel"] == "prova" and not r.get("duplicata_de_gid")]
for p in provas:
    for papel, campo in ((("padrao_resposta", "pad"), ("resolucao", "res")) if p["discursiva"] else
                         (("gabarito", "gab"), ("resolucao", "res"), ("padrao_resposta", "pad"))):
        cs = []
        for rel, g in candidatos(p, papel):
            s, bate = pontua(p, g, rel)
            cs.append((s, bate, g))
        cs.sort(key=lambda x: -x[0])
        if cs and cs[0][0] >= 4:
            p[campo] = cs[0][2]; p[campo + "_bate"] = cs[0][1]; p[campo + "_pontos"] = round(cs[0][0], 1)
            # empate: dois candidatos quase iguais -> dúvida
            if len(cs) > 1 and cs[1][0] >= cs[0][0] - 0.5: p[campo + "_duvida"] = True
    if not p.get("gab") and re.search(r"com gabarito", sa(p["nome"])):
        p["gab_embutido"] = True
    # resolução que traz o gabarito dentro serve de apoio, mas não é "gabarito oficial"

# ---------- cor de triagem
def triagem(p):
    mot = []
    q = p["q"]
    if p["discursiva"]:
        return "discursiva", ["prova discursiva (fica fora das três cores)"] + (["com padrão de resposta"] if p.get("pad") else [])
    if p["escaneado"]: mot.append("escaneado (sem texto)")
    if p.get("pad") and not p.get("gab"): mot.append("discursiva (só padrão de resposta)")
    elif p.get("gab_embutido"): mot.append("gabarito dentro da própria prova (conferir à parte)")
    elif not p.get("gab"): mot.append("sem gabarito ligado")
    if q[2] < 5 and not p["escaneado"] and p.get("gab_bate") != "sim": mot.append("questões não numeradas/encontradas")
    if mot and not (p.get("gab_embutido") and len(mot) == 1): return "vermelho", mot
    if p.get("gab_bate") == "não": mot.append("número de questões não bate com o gabarito")
    if p.get("gab_bate") == "?": mot.append("gabarito sem leitura automática (formato novo)")
    if p.get("gab_bate") == "contém": mot.append("gabarito cobre mais que a prova (outro dia/caderno junto)")
    if p.get("gab_duvida"): mot.append("dois gabaritos possíveis")
    if p.get("gab_bate") == "sim":
        gg = p["gab"]["g"]; P = numeros_prova(p)
        alem = sum(1 for n in range(gg[1] + 1, gg[1] + 21) if n in P)
        if alem >= 15: mot.append("prova parece ter mais questões que o gabarito (parte discursiva?)")
    if p.get("gab", {}).get("escaneado"): mot.append("gabarito escaneado")
    if p["frac_sem_texto"] > 0.2: mot.append(f"{p['pag_sem_texto']} páginas sem texto")
    if p.get("cid", 0) > 20 or p.get("pua", 0) > 50 or p.get("repl", 0) > 50: mot.append("símbolos desenhados/fonte sem mapa")
    if mot:
        grave = any(m.startswith(("número", "gabarito sem")) for m in mot)
        return ("vermelho" if grave else "amarelo"), mot
    return "verde", []

for p in provas:
    p["cor_triagem"], p["triagem_motivos"] = triagem(p)

# ---------- mesma prova em várias cores: fica uma (verde antes; azul preferida), as outras ficam de reserva
SEMCOR = re.compile(r"\b(azul|amarel\w*|branc\w*|rosa|cinza|verde|laranja|roxo|caderno\s*\d+|cad\s*\d+)\b")
def chave_cor(p):
    k = chaves(p["nome"])
    return (p["pasta"], SEMCOR.sub(" ", base_nome(p["nome"])).split().__str__(), k["dia"], k["fase"], k["mod"])
grupos = collections.defaultdict(list)
for p in provas:
    if chaves(p["nome"])["cor"] or re.search(r"caderno\s*\d", sa(p["nome"])): grupos[chave_cor(p)].append(p)
ORDEM = {"verde": 0, "amarelo": 1, "vermelho": 2, "discursiva": 3}
for lst in grupos.values():
    if len(lst) < 2: continue
    lst.sort(key=lambda p: (ORDEM[p["cor_triagem"]], chaves(p["nome"])["cor"] != "azul", p["nome"]))
    for p in lst[1:]: p["outra_cor_de"] = lst[0]["gid"]
# ENEM 2020-2025: já publicado inteiro (uma cor por prova); as outras cores ficam de reserva
for p in provas:
    a = ANO.findall(p["path"])
    if p["inst"] == "ENEM" and a and "2020" <= a[-1] <= "2025" and p["path"] not in drive2_cam:
        p["enem_publicado"] = True

# ---------- códigos P6000+ e saída por instituição
# códigos estáveis: quem já tem código num drive2_*.json mantém; novos continuam do maior
gid2pid = {}; usados = {}
for f in glob.glob(os.path.join(OUT, "drive2_*.json")):
    for d in json.load(open(f)): usados[d["drive_id"]] = d["id"]
k = max([ID0] + [int(v[1:]) + 1 for v in usados.values()])
for r in regs:
    if r["gid"] in usados: gid2pid[r["gid"]] = usados[r["gid"]]
for r in sorted(regs, key=lambda r: r["path"]):
    if r["path"] in drive2_cam or r.get("md5") in drive2_md5:
        gid2pid[r["gid"]] = drive2_cam.get(r["path"]) or drive2_md5[r["md5"]]; r["ja_catalogado"] = True; continue
    if r["gid"] in gid2pid: continue
    gid2pid[r["gid"]] = f"P{k}"; k += 1

STATUS = {"prova": "a extrair", "gabarito": "apoio (usado com a prova)", "resolucao": "apoio (usado com a prova)",
          "padrao_resposta": "apoio (usado com a prova)", "redacao": "ignorar (redação)", "auxiliar": "ignorar (sem questões)",
          "nao_pdf": "ignorar (não é PDF)", "erro": "erro no download"}
saida = collections.defaultdict(list)
for r in sorted(regs, key=lambda r: r["path"]):
    if r.get("ja_catalogado"): continue
    kk = chaves(r["nome"]); anos = ANO.findall(r["path"])
    e = {"id": gid2pid[r["gid"]], "status": STATUS[r["papel"]], "grupo": r["inst"], "vestibular": r["inst"],
         "topo": r["topo"], "ano": anos[-1] if anos else "", "dia": kk["dia"], "fase_etapa": kk["fase"],
         "caderno": kk["cor"], "papel": r["papel"], "gabarito_ids": "", "resolucao_ids": "", "padrao_ids": "",
         "duplicata_de": "", "paginas": r.get("paginas", 0), "tamanho_mb": round(r.get("bytes", 0) / 1e6, 2),
         "origem": "DRIVE2", "drive_id": r["gid"], "conjunto": "DRIVE NOVO/" + r["pasta"], "arquivo": r["nome"],
         "caminho": "DRIVE NOVO/" + r["path"], "md5": r.get("md5", "")}
    if r.get("papel_obs"): e["obs"] = "papel " + r["papel_obs"]
    if r.get("duplicata_de_gid"):
        e["duplicata_de"] = gid2pid[r["duplicata_de_gid"]]; e["tipo_duplicata"] = "arquivo idêntico (md5)"
        e["status"] = "ignorar (duplicata)"
    if r.get("md5") in antigo_md5: e["ja_no_drive_antigo"] = antigo_md5[r["md5"]]
    if r["papel"] not in ("nao_pdf", "erro"):
        e["texto"] = "escaneado" if r["escaneado"] else ("parcial" if r["frac_sem_texto"] > 0.1 else "ok")
        e["paginas_sem_texto"] = r["pag_sem_texto"]
        q = r["q"] if r["papel"] == "prova" else r["g"]
        if r["papel"] == "prova" and r.get("gab_bate") == "sim": q = r["gab"]["g"]
        e["questoes_faixa"] = f"{q[0]}-{q[1]}" if q[2] else ""; e["questoes_estimadas"] = q[2] or ""
    if r["papel"] == "prova" and not r.get("duplicata_de_gid"):
        for campo, alvo in (("gab", "gabarito_ids"), ("res", "resolucao_ids"), ("pad", "padrao_ids")):
            if r.get(campo): e[alvo] = gid2pid[r[campo]["gid"]]
        if r.get("gab"): e["gabarito_confere"] = r["gab_bate"]
        e["cor_triagem"] = r["cor_triagem"]; e["triagem_motivos"] = r["triagem_motivos"]
        if r.get("outra_cor_de"):
            e["outra_cor_de"] = gid2pid[r["outra_cor_de"]]; e["status"] = "reserva (outra cor da mesma prova)"
        if r.get("enem_publicado"):
            e["status"] = "reserva (ENEM deste ano já publicado em outra cor)"
    saida[r["inst"]].append(e)

def arq(inst):
    return re.sub(r"[^a-z0-9]+", "_", sa(inst)).strip("_") or "raiz"

for f in glob.glob(os.path.join(OUT, "drive2_*.json")): os.remove(f)
for inst, lst in saida.items():
    json.dump(lst, open(os.path.join(OUT, f"drive2_{arq(inst)}.json"), "w"), ensure_ascii=False, indent=1)

# ---------- resumo
res = {"arquivos": len(regs), "ja_catalogados_enem": sum(1 for r in regs if r.get("ja_catalogado")),
       "codigos": f"P{ID0}-P{k-1}", "dica": "para recomeçar a numeração, apague os drive2_*.json antes", "por_papel": collections.Counter(r["papel"] for r in regs),
       "repetidos": sum(1 for r in regs if r.get("duplicata_de_gid")),
       "ja_no_drive_antigo": sum(1 for r in regs if r.get("md5") in antigo_md5),
       "instituicoes": {}}
for inst, lst in sorted(saida.items(), key=lambda x: -len(x[1])):
    pv = [e for e in lst if e["papel"] == "prova" and e["status"] == "a extrair"]
    res["instituicoes"][inst] = {"arquivos": len(lst), "provas": len(pv),
        "reserva_outra_cor": sum(1 for e in lst if e["status"].startswith("reserva")),
        "ja_no_drive_antigo": sum(1 for e in pv if e.get("ja_no_drive_antigo")),
        "com_gabarito": sum(1 for e in pv if e["gabarito_ids"]),
        "gabarito_confere": sum(1 for e in pv if e.get("gabarito_confere") == "sim"),
        "verde": sum(1 for e in pv if e["cor_triagem"] == "verde"),
        "amarelo": sum(1 for e in pv if e["cor_triagem"] == "amarelo"),
        "vermelho": sum(1 for e in pv if e["cor_triagem"] == "vermelho"),
        "discursiva": sum(1 for e in pv if e["cor_triagem"] == "discursiva"),
        "motivos": collections.Counter(m for e in pv for m in e["triagem_motivos"]).most_common()}
os.makedirs(os.path.join(OUT, "resumo"), exist_ok=True)
json.dump(res, open(os.path.join(OUT, "resumo", "resumo_drive2.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "instituicoes"}, ensure_ascii=False))
for inst, v in res["instituicoes"].items():
    print(f"{inst[:30]:30} arq {v['arquivos']:4} provas {v['provas']:4} gab {v['com_gabarito']:4} confere {v['gabarito_confere']:4} "
          f"verde {v['verde']:4} amar {v['amarelo']:4} verm {v['vermelho']:4} disc {v['discursiva']:4}")
