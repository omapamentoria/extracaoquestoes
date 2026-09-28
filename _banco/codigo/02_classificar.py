# Banco MAPA - passo 2: classifica cada PDF do inventario e monta o catalogo.
# Entrada: _banco/inventario.jsonl  (+ _banco/legibilidade.jsonl, se existir)
# Saida:   _banco/catalogo.csv
import os, re, json, csv, unicodedata, collections

RAIZ = os.path.expanduser("~/mnt/BM")
B = os.path.join(RAIZ, "_banco")
DRIVE = "DRIVE ENEM + VEST - SIGAM @WAGNERNAMED"
MAPA = "O Mapa Mentoria"

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

SEM_QUESTOES = ["Livros literários", "Resumos", "Mapas mentais", "Cronogramas", "Kit organização",
                "Guia do Estudante", "Livros que li", "Checklist", "Diagnóstico de simulados",
                "Incidência ENEM", "Modelo de Cartão", "Redação Competências INEP",
                "Materiais coletânea Redações VUNESP", "ANKI"]
INST_SIM = [("fb", "Farias Brito"), ("h3x", "Hexag"), ("hexag", "Hexag"), ("s0m", "Somos"), ("somos", "Somos"),
            ("p0l", "Poliedro"), ("poli", "Poliedro"), ("poly", "Poliedro"), ("objectiv", "Objetivo"),
            ("objetiv", "Objetivo"), ("bernoulli", "Bernoulli"), ("b3rn", "Bernoulli"), ("berno", "Bernoulli"),
            ("sas", "SAS"), ("s4s", "SAS")]
DISC = [("lingua estrangeira", "Língua Estrangeira"), ("lingua portuguesa instrumental", "Português Instrumental"),
        ("portugues e literatura", "Português e Literatura"), ("lingua portuguesa", "Português"),
        ("portugu", "Português"), ("literatura", "Literatura"), ("redac", "Redação"), ("biolog", "Biologia"),
        ("fisica", "Física"), ("quimica", "Química"), ("matem", "Matemática"), ("historia", "História"),
        ("geografia", "Geografia"), ("filosofia", "Filosofia"), ("sociologia", "Sociologia"),
        ("ingles", "Inglês"), ("espanhol", "Espanhol"), ("frances", "Francês"), ("arte", "Arte"),
        ("ciencias humanas", "Ciências Humanas"), ("ciencias da natureza", "Ciências da Natureza"),
        ("linguagens", "Linguagens")]
CORES = ["amarel", "azul", "branc", "rosa", "cinza", "verde", "laranja", "roxo"]
# pastas que nao definem o "conjunto" (a prova-mae fica acima delas)
SUBPASTAS_AUX = re.compile(r"^(gabaritos?|resolu[cç][aã]o.*|coment[aá]rios|gabaritos e coment[aá]rios|cadernos( e gabaritos)?|"
                           r"primeiro dia|segundo dia|[12][ºo°]? dia( de prova)?|dia 0?[12]|l[ií]nguas? estrangeiras?|"
                           r"provas-e-gabaritos.*)$", re.I)

def ano_de(partes):
    for p in reversed(partes):
        m = re.findall(r"(?<!\d)(199[89]|20[0-2]\d)(?!\d)", p)
        if m: return m[0]
    return ""

def instituicao_sim(txt):
    t = sem_acento(txt)
    for k, v in INST_SIM:
        if k in t: return v
    return ""

def papel_de(nome, secao):
    n = sem_acento(nome)
    if re.search(r"folha de reda|cartao|modelo gab|modelo folha", n): return "auxiliar"
    if re.search(r"\((com|sem)\s+gabarito\)", n): return "prova"
    if re.search(r"resposta[s]?[ -_]esperada|resp cienc|resposta ciencia|^resp[ _]", n): return "padrao_resposta"
    if re.search(r"criterio|grade de correcao|expectativa|padrao de resposta|respostas esperadas", n): return "padrao_resposta"
    if "exame discursivo" in n and "respostas" in n: return "padrao_resposta"
    if "errata" in n: return "auxiliar"
    if re.search(r"respost", n) and re.search(r"discursiv|2\s*[aª]?\s*fase|segunda fase", sem_acento(secao)): return "padrao_resposta"
    if re.search(r"resolu|coment|respost|correcao|^res_|_res_|cmtd", n): return "resolucao"
    if re.search(r"gab|(^|[_\W])gb[_\W]", n): return "gabarito"
    return "prova"

def dia_de(txt):
    t = sem_acento(txt)
    t = re.sub(r"[_\-]+", " ", t)
    if re.search(r"primeiro dia|1\s*[ºo°]?\s*dia|dia\s*0?1\b|(^|[^a-z0-9])d1([^0-9]|$)|_1o?dia|1odia", t): return "1"
    if re.search(r"segundo dia|2\s*[ºo°]?\s*dia|dia\s*0?2\b|(^|[^a-z0-9])d2([^0-9]|$)|_2o?dia|2odia", t): return "2"
    if re.search(r"3\s*[ºo°]?\s*dia|dia\s*0?3\b", t): return "3"
    return ""

def fase_de(txt):
    t = sem_acento(txt)
    if re.search(r"(1\s*[aªº°o]?\s*fase|primeira fase|fase\s*1|_1fase)", t): return "1ª fase"
    if re.search(r"(2\s*[aªº°o]?\s*fase|segunda fase|fase\s*2|_2fase)", t): return "2ª fase"
    if re.search(r"1\s*[ºo°]?\s*exame|1[ºo°]? eq|primeiro exame", t): return "1º exame de qualificação"
    if re.search(r"2\s*[ºo°]?\s*exame|2[ºo°]? eq|segundo exame", t): return "2º exame de qualificação"
    if "exame discursivo" in t: return "exame discursivo"
    return ""

def caderno_de(txt):
    t = sem_acento(txt)
    for c in CORES:
        if c in t: return {"amarel": "amarelo", "branc": "branco"}.get(c, c)
    m = re.search(r"tipo[\s_-]*([a-e1-9])\b", t) or re.search(r"prova[_\s-]([a-e])(\b|-)", t) or re.search(r"caderno[_\s-]*(\d+)", t)
    if m: return "tipo " + m.group(1).upper()
    return ""

def disciplina_de(nome):
    n = sem_acento(nome)
    for k, v in DISC:
        if k in n: return v
    return ""

def classifica(r):
    cam = r["caminho"]; partes = cam.split("/"); nome = partes[-1]
    raiz, secao = partes[0], partes[1] if len(partes) > 1 else ""
    sub = "/".join(partes[2:-1])
    s = sem_acento(cam)
    d = dict(origem="DRIVE" if raiz == DRIVE else "MAPA", grupo="", tipo_fonte="", vestibular="",
             instituicao="", ano=ano_de(partes[1:]), edicao="", fase_etapa="", dia="", caderno="",
             disciplina="", simulado_n="", papel="", nivel="", obs="")
    txt_ctx = "/".join(partes[2:])  # sem o nome da pasta-raiz

    nl = sem_acento(nome)
    NAO_PROVA = r"concorrencia|notas[_ -]classific|panilha|planilha|edital|resultado|manual do candidato|leia aqui|agenda|cronog|checklist|check list|plano 1000|cartilha|incidencia|analise"
    if raiz == DRIVE and len(partes) == 3 and secao.startswith("Materiais "):
        if re.search(r"rpa|miolo|semelhantes|vestibulares_paulistas|supertop|stood|arquivo unico|revisao", nl):
            d.update(grupo="COMPILACAO", tipo_fonte="compilado", vestibular=secao.replace("Materiais ", "").replace("^", ""))
            return d
        if r["paginas"] <= 2 or re.search(NAO_PROVA, nl):
            d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes"); return d
    if re.search(NAO_PROVA, nl) and not re.search(r"prova|questo|simulado", nl):
        d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes"); return d
    if raiz == DRIVE and len(partes) == 2:
        d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes")
    elif raiz == DRIVE and any(secao.startswith(x) for x in SEM_QUESTOES):
        d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes")
    elif raiz == DRIVE and secao == "Provas ENEM normal e ENEM PPL" or raiz == MAPA and sub.startswith("Provas antigas-Enem"):
        d.update(grupo="ENEM", tipo_fonte="prova_oficial", vestibular="ENEM")
    elif raiz == DRIVE and secao.startswith("Simulados") or raiz == MAPA and sub.startswith("Simulados SAS"):
        d.update(grupo="SIMULADO_ENEM", tipo_fonte="simulado", vestibular="ENEM",
                 instituicao=instituicao_sim(partes[2] if raiz == DRIVE else "sas"))
    elif raiz == MAPA and secao == "SSA MATERIAL":
        d.update(vestibular="SSA")
        m = re.search(r"SSA ?([123])(?!\d)", cam)
        if m: d["fase_etapa"] = f"SSA {m.group(1)}"
        m = re.search(r"(\d)[\s_-]*dia[\s_-]*(\d)[\s_-]*etapa", sem_acento(nome))
        if m: d["fase_etapa"] = f"SSA {m.group(2)}"; d["_dia_fixo"] = m.group(1)
        m = re.search(r"([123])\s*fase", sem_acento(nome))
        if m and "SIMULADOS" in sub: d["fase_etapa"] = f"SSA {m.group(1)}"
        if "PROVAS ANTIGAS" in sub or "Provas antigas-SSA" in sub:
            d.update(grupo="SSA", tipo_fonte="prova_oficial")
        elif "SIMULADOS" in sub:
            d.update(grupo="SIMULADO_SSA", tipo_fonte="simulado", instituicao="SAS")
        elif "APOSTILAS" in sub:
            d.update(grupo="APOSTILA", tipo_fonte="apostila")
        else:
            d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes")
    elif raiz == DRIVE and secao == "Provas ENCCEJA":
        d.update(grupo="ENCCEJA", tipo_fonte="prova_oficial", vestibular="ENCCEJA",
                 nivel="fundamental" if "FUND" in cam else ("médio" if "MÉDIO" in cam else ""))
    elif raiz == DRIVE and secao.startswith("Materiais "):
        vest = secao.replace("Materiais ", "").replace("^", "").strip()
        d["vestibular"] = vest
        sl = sem_acento(sub + "/" + nome)
        if re.search(r"obras|livros|analises|redacao uerj|conteudo programatico|historia e geografia do mt", sl):
            d.update(grupo="SEM_QUESTOES", tipo_fonte="sem_questoes")
        elif re.search(r"simulad|simu ", sl):
            d.update(grupo="SIMULADO_" + vest.upper(), tipo_fonte="simulado", instituicao=instituicao_sim(sub))
        elif re.search(r"por assunto|por materia|assuntos mais cobrados|questoes por assunto", sl) or vest == "FUVEST" and len(partes) == 3:
            d.update(grupo="COMPILACAO", tipo_fonte="compilado")
        elif re.search(r"apostila|revisao|matematica ufms|super apostila", sl):
            d.update(grupo="APOSTILA", tipo_fonte="apostila")
        elif "provas uss" in sl:
            d.update(grupo="DEMAIS", tipo_fonte="prova_oficial", vestibular="USS")
        elif len(partes) == 3:
            d.update(grupo="REVISAR", tipo_fonte="?")
        else:
            big = {"FUVEST", "UNICAMP", "UERJ", "UNESP"}
            d.update(grupo=vest.upper() if vest.upper() in big else "DEMAIS", tipo_fonte="prova_oficial")
    elif raiz == DRIVE and secao in ("Habilidades ENEM c- questões", "Questões pré-teste enem",
                                     "Raio X do ENEM c- questões", "Questões ENEM por nível de dificuldade",
                                     "Clássicos para o Vestibular"):
        d.update(grupo="COMPILACAO", tipo_fonte="compilado", vestibular="ENEM" if "ENEM" in secao.upper() or "enem" in secao else "")
    elif raiz == DRIVE and secao in ("Enem - Apostilas", "Revisão (muitos materiais)", "Matemática do zero",
                                     "FÓRMULAS E TABELAS IMPORTANTES", "Livros didáticos famosos"):
        d.update(grupo="APOSTILA", tipo_fonte="apostila")
    else:
        d.update(grupo="REVISAR", tipo_fonte="?")

    if d["tipo_fonte"] in ("prova_oficial", "simulado"):
        d["papel"] = papel_de(nome, txt_ctx)
        # arquivo de gabarito dentro de pasta "Gabarito"
        if d["papel"] == "prova" and re.search(r"/gabaritos?(/|$)", sem_acento("/".join(partes[:-1]))):
            d["papel"] = "gabarito"
        if d["papel"] == "prova" and re.search(r"resolu|coment", sem_acento(partes[-2])):
            d["papel"] = "resolucao"
        d["dia"] = d.pop("_dia_fixo", "") or dia_de(txt_ctx)
        if not d["fase_etapa"]: d["fase_etapa"] = fase_de(txt_ctx)
        d["caderno"] = caderno_de(nome)
        if d["tipo_fonte"] == "prova_oficial" and d["vestibular"] not in ("ENEM", "ENCCEJA"):
            d["disciplina"] = disciplina_de(nome)
        if d["vestibular"] == "ENCCEJA":
            d["disciplina"] = disciplina_de(nome)
        e = sem_acento(txt_ctx)
        e = re.sub(r"normal e (reaplicacao|3. aplicacao)", "", e)
        e = re.sub(r"(1\s*[°ºª]?\s*aplicacao|primeira aplicacao|1\s*[°º]?\s*apli\b)", "", e)
        ed = []
        if "ppl" in e: ed.append("PPL")
        if "reaplica" in e or "2 aplicacao" in e or "2° aplica" in e or "2º aplica" in e or "segunda aplica" in e: ed.append("reaplicação")
        if "terceira aplica" in e or "3ª aplica" in e or "3a aplica" in e: ed.append("3ª aplicação")
        if "digital" in e: ed.append("digital")
        if "impresso" in e: ed.append("impresso")
        if "cop30" in e: ed.append("COP30-Belém")
        if "fraudada" in e: ed.append("prova vazada (2009)")
        if "(com gabarito)" in sem_acento(nome) or "(com  gabarito)" in sem_acento(nome): d["obs"] = "caderno com gabarito marcado"
        m = re.search(r"(20\d\d)[.\-\s]+([12])(?!\d)", sem_acento(partes[-2] if len(partes) > 2 else ""))
        if m and d["vestibular"] in ("UERJ", "UNEMAT", "FATEC"): ed.append(f"{m.group(1)}.{m.group(2)}")
        if d["vestibular"] == "ENEM" and ("PPL" in ed or "reaplicação" in ed):
            ed = ["PPL/reaplicação"] + [x for x in ed if x not in ("PPL", "reaplicação")]
        d["edicao"] = ", ".join(dict.fromkeys(ed)) or ("regular" if d["tipo_fonte"] == "prova_oficial" else "")
        nl2 = sem_acento(nome)
        var = []
        m = re.search(r"grupo\s*(\d)", nl2)
        if m: var.append("grupo " + m.group(1))
        for k, v in (("biologicas", "área biológicas"), ("exatas", "área exatas"), ("humanas-artes", "área humanas"), ("humanas artes", "área humanas"),
                     ("(medicina)", "medicina"), ("todos os cursos", "demais cursos"), ("frances", "francês"), ("espanhol", "espanhol"), ("ingles", "inglês")):
            if k in nl2 and v not in var: var.append(v)
        m = re.search(r"prova[\s_-]?(\d)\.pdf", nl2)
        if m and d["vestibular"] in ("UNICAMP",): var.append("prova " + m.group(1))
        d["variante"] = ", ".join(var)
        if d["tipo_fonte"] == "simulado":
            pasta = partes[-2] if len(partes) > 2 else ""
            nums = [n for n in re.findall(r"\d+", pasta) if len(n) <= 2]
            if not nums: nums = [n for n in re.findall(r"(\d+)\s*[ºo°]", nome)]
            if not nums and "extra" in sem_acento(pasta): nums = ["extra"]
            d["simulado_n"] = nums[0] if nums else ""
    return d

# ---------------------------------------------------------------- execucao
rs = [json.loads(l) for l in open(os.path.join(B, "inventario.jsonl"), encoding="utf-8")]
CAM_ORIG = {}
for r in rs:
    n = unicodedata.normalize("NFC", r["caminho"]); CAM_ORIG[n] = r["caminho"]; r["caminho"] = n
leg = {}
lp = os.path.join(B, "legibilidade.jsonl")
if os.path.exists(lp):
    for l in open(lp, encoding="utf-8"):
        x = json.loads(l); leg[unicodedata.normalize("NFC", x["caminho"])] = x

rs.sort(key=lambda r: (0 if r["caminho"].startswith(DRIVE) else 1, r["caminho"]))
linhas = []
for i, r in enumerate(rs, 1):
    d = classifica(r)
    d["id"] = f"P{i:04d}"
    d["caminho"] = CAM_ORIG[r["caminho"]]; d["_cam"] = r["caminho"]; d["arquivo"] = os.path.basename(r["caminho"])
    d["paginas"] = r["paginas"]; d["tamanho_mb"] = round(r["tamanho"] / 1e6, 1); d["md5"] = r["md5"]
    ch = r["chars_amostra"] or [0]
    L = leg.get(r["caminho"])
    if L:
        d["texto"] = L["texto"]; d["paginas_problema"] = L.get("paginas_problema", "")
        npb = sum((int(b) - int(a) + 1) if "-" in x else 1 for x in d["paginas_problema"].split(",") if x for a, b in [(x.split("-") + [x])[:2]])
        if d["texto"] == "parcialmente corrompido" and npb <= 2 and npb < 0.1 * max(1, r["paginas"]):
            d["texto"] = "ok"
        if L.get("paginas_vazias") and d["texto"].startswith("ok"):
            d["paginas_sem_texto"] = L["paginas_vazias"]
    else:
        if max(ch) < 50: d["texto"] = "sem_texto (imagem)"
        elif r["legib"] is not None and r["legib"] < 0.10: d["texto"] = "corrompido"
        elif r["legib"] is not None and r["legib"] < 0.20: d["texto"] = "duvidoso"
        else: d["texto"] = "ok"
        d["paginas_problema"] = ""
    d["_trecho"] = r["trecho"][:600]
    linhas.append(d)

# conjunto = pasta da prova, subindo as subpastas auxiliares (Gabarito, Primeiro dia, Resolução...)
for d in linhas:
    ps = d["_cam"].split("/")[:-1]
    while len(ps) > 2 and SUBPASTAS_AUX.match(ps[-1].strip()):
        ps = ps[:-1]
    d["conjunto"] = "/".join(ps)

# arquivo "X.pdf" ao lado de "X_prova....pdf": X e a resolucao comentada (traz questoes + respostas)
por_pasta = collections.defaultdict(list)
for d in linhas: por_pasta[os.path.dirname(d["_cam"])].append(d)
for ds in por_pasta.values():
    stems = [os.path.splitext(x["arquivo"])[0].lower() for x in ds]
    for d, st in zip(ds, stems):
        if d["papel"] == "prova" and any(o != st and o.startswith(st + "_prova") for o in stems):
            d["papel"] = "resolucao"; d["obs"] = (d["obs"] + "; " if d["obs"] else "") + "resolução com as questões (há arquivo _prova ao lado)"

# pareamento prova <-> gabarito / resolucao dentro do conjunto
def compat(a, b, campo):
    return not a[campo] or not b[campo] or a[campo] == b[campo]
por_conj = collections.defaultdict(list)
for d in linhas:
    if d["tipo_fonte"] in ("prova_oficial", "simulado"): por_conj[d["conjunto"]].append(d)
for conj, ds in por_conj.items():
    for p in [d for d in ds if d["papel"] == "prova"]:
        for papel, campo in (("gabarito", "gabarito_ids"), ("resolucao", "resolucao_ids"), ("padrao_resposta", "padrao_ids")):
            cand = [g for g in ds if g["papel"] == papel and all(compat(p, g, c) for c in ("ano", "simulado_n", "dia", "fase_etapa", "disciplina", "variante", "caderno"))]
            if not cand:
                cand = [g for g in ds if g["papel"] == papel and all(compat(p, g, c) for c in ("ano", "simulado_n", "dia", "fase_etapa", "disciplina", "variante"))]
            p[campo] = [g["id"] for g in cand]
        if not p["gabarito_ids"] and p.get("obs") == "caderno com gabarito marcado":
            p["gabarito_ids"] = ["(no próprio caderno)"]

def nota(d, txt):
    d["obs"] = (d["obs"] + "; " if d["obs"] else "") + txt

# ---- duplicatas
POR_ID = {d["id"]: d for d in linhas}
def rank(d):  # qual copia fica como principal
    return (0 if d["texto"].startswith("ok") else 1,
            0 if d.get("gabarito_ids") else 1,
            0 if "com gabarito" not in d["obs"] else 1,
            0 if d["origem"] == "DRIVE" else 1,
            d["caminho"])
uf = {d["id"]: d["id"] for d in linhas}
def raiz_(x):
    while uf[x] != x: uf[x] = uf[uf[x]]; x = uf[x]
    return x
def une(a, b, tipo):
    ra, rb = raiz_(a), raiz_(b)
    if ra != rb: uf[rb] = ra
    POR_ID[a].setdefault("_tipos", set()).add(tipo); POR_ID[b].setdefault("_tipos", set()).add(tipo)
por_md5 = collections.defaultdict(list)
for d in linhas: por_md5[d["md5"]].append(d["id"])
for ids in por_md5.values():
    for x in ids[1:]: une(ids[0], x, "arquivo idêntico")
POR_CAM = {d["caminho"]: d for d in linhas}
def chave(d):
    return (d["vestibular"], d["ano"], d["edicao"], d["fase_etapa"], d["dia"], d["disciplina"], d["instituicao"], d["simulado_n"], d.get("variante", ""))
sp = os.path.join(B, "similares.jsonl")
if os.path.exists(sp):
    for l in open(sp, encoding="utf-8"):
        x = json.loads(l); a, b = POR_CAM.get(x["a"]), POR_CAM.get(x["b"]); j = x["jaccard"]
        if not a or not b: continue
        jv = x.get("vocab", 0)
        mesmo_papel = a["papel"] == b["papel"]
        exame = a["tipo_fonte"] in ("prova_oficial", "simulado") and b["tipo_fonte"] in ("prova_oficial", "simulado")
        dias_dif = a["dia"] and b["dia"] and a["dia"] != b["dia"]
        if exame and mesmo_papel and a["papel"] == "prova" and chave(a) == chave(b) and (jv >= 0.8 or j >= 0.5):
            une(a["id"], b["id"], "mesma prova (outro caderno/cor ou outro arquivo)")
        elif mesmo_papel and j >= 0.9 and jv >= 0.9 and not dias_dif and (not exame or a["ano"] == b["ano"]):
            une(a["id"], b["id"], "conteúdo igual (outra cópia)")
        elif exame and (j >= 0.5 or (dias_dif and jv >= 0.8)) and (chave(a) != chave(b) or dias_dif):
            if dias_dif: t = "conteúdo quase igual ao de {} , que é de OUTRO DIA ({}%) — conferir se o arquivo está trocado"
            else: t = "conteúdo parecido com {} ({}%) — conferir"
            nota(a, t.format(b["id"], int(max(j, jv) * 100))); nota(b, t.format(a["id"], int(max(j, jv) * 100)))
grupos = collections.defaultdict(list)
for d in linhas: grupos[raiz_(d["id"])].append(d)
for g in grupos.values():
    if len(g) < 2: continue
    g.sort(key=rank); princ = g[0]
    for d in g[1:]:
        d["duplicata_de"] = princ["id"]; d["tipo_duplicata"] = " / ".join(sorted(d.get("_tipos", [])))
    # gabaritos/resolucoes das copias passam para a principal
    for campo in ("gabarito_ids", "resolucao_ids", "padrao_ids"):
        todos = list(princ.get(campo) or [])
        for d in g[1:]:
            for x in d.get(campo) or []:
                if x not in todos: todos.append(x)
        if todos: princ[campo] = todos
for d in linhas:
    for campo in ("gabarito_ids", "resolucao_ids", "padrao_ids"):
        v = d.get(campo) or []
        # aponta para a copia principal de cada gabarito
        vv = []
        for x in v:
            orig = x
            x = POR_ID[x].get("duplicata_de") or x if x in POR_ID else x
            if x == d["id"] or (x in POR_ID and POR_ID[x]["papel"] == "prova" and campo == "gabarito_ids"):
                nota(d, f"o arquivo de gabarito {orig} é na verdade uma cópia da prova (gabarito real ausente)")
                continue
            if x not in vv: vv.append(x)
        d[campo] = " ".join(vv)

PRIO = {"ENEM": 1, "SSA": 2, "SIMULADO_ENEM": 3, "SIMULADO_SSA": 3, "FUVEST": 4, "UNICAMP": 4, "UERJ": 4, "UNESP": 4,
        "DEMAIS": 5, "COMPILACAO": 7, "APOSTILA": 8, "ENCCEJA": 9}
for d in linhas:
    g = d["grupo"]
    d["prioridade"] = PRIO.get(g, 6 if g.startswith("SIMULADO_") else "")
    if g == "ENCCEJA" and d["nivel"] == "fundamental": d["prioridade"] = 10
    if g == "SEM_QUESTOES": d["status"] = "ignorar (sem questões)"; d["prioridade"] = ""
    elif d.get("duplicata_de"): d["status"] = "ignorar (duplicata)"
    elif d["tipo_fonte"] in ("prova_oficial", "simulado") and d["papel"] != "prova": d["status"] = "apoio (usado com a prova)"
    elif g == "REVISAR": d["status"] = "revisar classificação"
    else: d["status"] = "a extrair"
    if d["status"] == "a extrair" and d["tipo_fonte"] in ("prova_oficial", "simulado") and not (d["gabarito_ids"] or d["resolucao_ids"] or d["padrao_ids"]):
        nota(d, "sem gabarito/resolução pareado")
    if d["status"] == "apoio (usado com a prova)":
        usado = any(d["id"] in (x.get("gabarito_ids", "") + " " + x.get("resolucao_ids", "") + " " + x.get("padrao_ids", "")).split() for x in linhas)
        if not usado: nota(d, "não pareado com nenhuma prova")

# estimativa do nº de questoes (so para planejamento): maior numero de "Questão N" distinto no texto
import gzip
RQ = re.compile(r"(?:QUEST[ÃA]O|Quest[ãa]o|QUESTÃO)\s*[:nNº°.-]*\s*0*(\d{1,3})\b")
for d in linhas:
    if d["status"] != "a extrair": continue
    p = os.path.join(B, "texto", d["md5"] + ".txt.gz")
    if not os.path.exists(p): continue
    t = gzip.open(p, "rt", encoding="utf-8").read()
    nums = {int(x) for x in RQ.findall(t) if 0 < int(x) <= 300}
    alt_e = len(re.findall(r"(?m)^\s*(?:\(E\)|E\)|e\)|\(e\))\s", t))
    est = max(len(nums), alt_e)
    if est >= 3: d["questoes_estimadas"] = est

COLS = ["id", "status", "prioridade", "grupo", "tipo_fonte", "vestibular", "instituicao", "ano", "edicao", "fase_etapa",
        "dia", "caderno", "disciplina", "variante", "nivel", "simulado_n", "papel", "gabarito_ids", "resolucao_ids", "padrao_ids",
        "duplicata_de", "tipo_duplicata", "texto", "paginas_problema", "paginas_sem_texto", "paginas", "questoes_estimadas", "tamanho_mb", "obs", "origem",
        "conjunto", "arquivo", "caminho", "md5"]
with open(os.path.join(B, "catalogo.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore", delimiter=";")
    w.writeheader()
    for d in linhas: w.writerow({k: d.get(k, "") for k in COLS})
json.dump([{k: d.get(k, "") for k in COLS + ["_trecho"]} for d in linhas],
          open(os.path.join(B, "catalogo_debug.json"), "w", encoding="utf-8"), ensure_ascii=False)
c = collections.Counter((d["grupo"], d["status"]) for d in linhas)
for k, v in sorted(c.items()): print(v, *k)
