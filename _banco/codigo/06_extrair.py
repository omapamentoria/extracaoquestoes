# Banco MAPA - passo 6: extrai as questoes de UMA prova (copia fiel).
# Uso: python3 06_extrair.py <id_prova_no_catalogo> [perfil: enem|ssa]
# Saida: _banco/questoes/<vestibular>/<ano>/<id_prova>/  (questoes.json, textos_base.json, img/*.png, revisao/*.jpg)
#
# Regras (ver banco-questoes-produto-final.md): o texto e copiado exatamente como esta no PDF; figuras sao
# recortadas da pagina; nada e inventado. Tudo o que o codigo nao consegue garantir vira "alerta" para revisao.
import os, sys, re, json, gzip, subprocess, collections, unicodedata, shutil, hashlib
import pdfplumber
import numpy as np
import cv2

RAIZ = os.path.expanduser("~/mnt/BM"); B = os.path.join(RAIZ, "_banco")
PID = sys.argv[1]; PERFIL = sys.argv[2] if len(sys.argv) > 2 else "auto"   # auto: o proprio codigo reconhece o formato da prova
CAT = {d["id"]: d for d in json.load(open(os.path.join(B, "catalogo_debug.json"), encoding="utf-8"))}
P = CAT[PID]
PDF = os.path.join(RAIZ, P["caminho"])
OUT = os.path.join(B, "questoes", P["vestibular"] or "outros", P["ano"] or "sem_ano", PID)
os.makedirs(os.path.join(OUT, "img"), exist_ok=True); os.makedirs(os.path.join(OUT, "revisao"), exist_ok=True)
DPI_FIG = 300; DPI_DET = 100
RE_Q_ENEM = re.compile(r"^(?i:quest[ãa]o)\s+0*(\d{1,3})\b")   # "QUESTÃO 91", "Questão 04" (ENEM 2019-2021), "QUESTãO 01" (versalete, ENEM 2025); sempre em negrito
RE_Q_NUM = re.compile(r"^0*(\d{1,3})\s*[.)–-]\s+\S")
RE_IDIOMA = re.compile(r"(?i)(op[çc][ãa]o|opci[óo]n)\W*(de\W*)?(l[íi]ngua\W*)?(estrangeira\W*)?(ingl[êe]s|espanhol|español)")
RE_AREA = re.compile(r"(?i)^(CI[ÊE]NCIAS|MATEM[ÁA]TICA|LINGUAGENS|QUEST[ÕO]ES DE)\b")
# "Texto para as questoes 02 e 03", "TEXTO PARA AS QUESTOES DE 04 A 06"
RE_PARA_Q = re.compile(r"(?i)\b(?:quest(?:ões|oes|ão|ao|ions?|iones?))\s+(?:de\s+|from\s+|n[ºo°]\s*)?0*(\d{1,3})(?:\s*(?:a|e|and|to|y|-|–|,)\s*0*(\d{1,3}))?\b")
def rotulo_faixa(t):
    """numeros das questoes de um rotulo de texto em frase ("Observe a imagem e leia o texto, para responder as questoes
    de 14 a 16"; "Leia o texto para responder a questao 18"), senao None"""
    if len(t) > 160 or not re.search(r"(?i)\b(respond\w*|answer|texto|textos|leia|considere|observe|analise|baseie|com base|refer\w*)\b", t): return None
    m = RE_PARA_Q.search(t)
    if not m or not (re.search(r"(?i)(para|to)\s+(as\s+|a\s+|the\s+)?(respond|answer|quest)", t) or re.match(r"(?i)^\W*(as|a)\s+quest\w*\s+\d.*\brefer", t)): return None
    return [int(x) for x in m.groups() if x]
RE_TEXTO_PARA = re.compile(r"(?i)^\W*(textos?|texts?|leia o texto|leia os textos|texto comum)\b.{0,40}?(quest|cuesti)\w*\W+(?:de\s+|from\s+)?((?:\d{1,3}\W*(?:and|to|e|a|y|-|–|,)?\W*)+)")

TMP = os.path.expanduser("~/tmp_banco"); os.makedirs(TMP, exist_ok=True)

# ------------------------------------------------------------------ vocabulario (para hifenizacao)
VOC_P = os.path.join(B, "vocab.json.gz")
def carrega_vocab():
    if os.path.exists(VOC_P):
        return collections.Counter(json.load(gzip.open(VOC_P, "rt", encoding="utf-8")))
    c = collections.Counter()
    for d in CAT.values():
        if d["status"] != "a extrair" or d["grupo"] not in ("ENEM", "SSA", "SIMULADO_ENEM", "FUVEST", "UNICAMP", "UERJ"): continue
        p = os.path.join(B, "texto", d["md5"] + ".txt.gz")
        if os.path.exists(p):
            c.update(w.lower() for w in re.findall(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*", gzip.open(p, "rt", encoding="utf-8").read()))
    json.dump({k: v for k, v in c.items() if v >= 2}, gzip.open(VOC_P, "wt", encoding="utf-8"))
    return c
VOC = carrega_vocab()

def junta_hifen(a, b):
    """a termina com '-' no fim da linha; b e o comeco da linha seguinte. Devolve (texto, duvida)."""
    wa = re.findall(r"[A-Za-zÀ-ÿ]+-$", a); wb = re.findall(r"^[A-Za-zÀ-ÿ]+", b)
    if not wa or not wb: return a + b, False
    s1, s2 = wa[0][:-1].lower(), wb[0].lower()
    junto, hif = VOC.get(s1 + s2, 0), VOC.get(s1 + "-" + s2, 0)
    if junto > hif: return a[:-1] + b, False
    if hif > junto: return a + b, False
    return a + b, True   # nao da para saber: mantem o hifen e marca para revisao

# ------------------------------------------------------------------ estilo
def estilo(fontname):
    f = fontname.lower()
    return ("bold" in f or "black" in f or "heavy" in f or "semibold" in f,
            "italic" in f or "oblique" in f)
ALT_PONTO = False      # a prova marca as alternativas com "A." (definido depois de ler todas as paginas)
ESTILO_Q = None        # como a prova numera as questoes: "questao" (QUESTAO 91), "ponto" (10. texto), "solto" (numero sozinho na linha)
def letra_alt(l):
    """Letra (A-E) se a linha comeca com marcador de alternativa: bolinha do ENEM, "a)", "(A)" ou "A." (so em prova
    que usa esse formato). Regra unica usada por todo o codigo (figuras, leitura, montagem)."""
    w0 = l["ws"][0]
    if eh_bolinha(w0["fontname"]) and re.fullmatch(r"([A-Ea-e])\1?", w0["text"]): return w0["text"][0].upper()
    t = txt_puro(l)
    m = re.match(r"^\(?([a-eA-E])\)(\s|$)", t)
    if m: return m.group(1).upper()
    if ALT_PONTO:
        m = re.match(r"^([A-E])\.(\s|$)", t)
        if m: return m.group(1)
    return None
def eh_codigo_tok(x):
    """codigo interno de questao de simulado (ex.: "R387", "196SE02BIO2019II", "BAN_027SE01FIS2018I")"""
    return re.fullmatch(r"[A-Z0-9_]{4,}", x) is not None and re.search(r"\d", x) is not None and re.search(r"[A-Z]", x) is not None
def cand_cabecalho(l):
    """[(estilo, numero)] que esta linha pode ser, como inicio de questao"""
    ws = l["ws"]; t = txt_puro(l).strip(); out = []
    m = RE_Q_ENEM.match(t)
    if m and ws[0]["bold"] and (len(ws) < 2 or ws[1]["bold"]): out.append(("questao", int(m.group(1))))
    m = RE_Q_NUM.match(t)
    if m and not l.get("pequena"): out.append(("ponto", int(m.group(1))))
    if len(ws) == 1 and re.fullmatch(r"0*\d{1,3}", t) and ws[0]["bold"] and 0.85 * CORPO <= l["size"] <= 2 * CORPO: out.append(("solto", int(t)))
    return out
def eh_cabecalho(l):
    """numero da questao se a linha e o cabecalho de uma questao (no formato desta prova), senao None"""
    if ESTILO_Q is None: return None
    for e, n in cand_cabecalho(l):
        if e == ESTILO_Q:
            if CAB_OK is not None and l.get("pg") is not None and (n, l["pg"]) not in CAB_OK: return None
            return n
    return None
CAB_OK = None
def linha_estrutural(l):
    """linha que organiza a prova (cabecalho de questao, alternativa, rotulo de texto, titulo de area, opcao de lingua):
    nunca vira parte de figura"""
    t = txt_puro(l).strip()
    return bool(letra_alt(l) or eh_cabecalho(l) is not None or RE_TEXTO_PARA.match(t)
                or (len(t) < 40 and re.match(r"(?i)^\W*texto\s+(\d{1,2}|[IVX]{1,4})\b", t))     # "Texto 2": titulo do proximo texto
                or (len(t) < 90 and (RE_AREA.match(t) or RE_IDIOMA.search(t))))
def eh_bolinha(fontname):   # letras das alternativas do ENEM (fonte de simbolos)
    f = fontname.lower().split("+")[-1]
    return "bundesbahn" in f or "dingbat" in f or "zapf" in f or re.search(r"pi(std)?[-_]?\d", f) is not None

# ------------------------------------------------------------------ leitura das paginas
pdf = pdfplumber.open(PDF)
NPAG = len(pdf.pages)

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "glifos_t3.py"), encoding="utf-8").read())
INVISIVEIS = {}
# "(cid:N)" de fonte sem tabela de texto (ToUnicode) mas com a numeracao ORIGINAL dos glifos (Arial do ENEM 2017-2018):
# o caractere vem de _banco/cid_unicode.json (montado de PDFs com a mesma fonte e com tabela; ferramentas_nuvem/tabela_cid.py).
# Trava: so vale na pagina se as palavras traduzidas existem no vocabulario (senao a fonte foi renumerada e fica PENDENTE).
_CID_P = os.path.join(B, "cid_unicode.json")
CID_TAB = json.load(open(_CID_P, encoding="utf-8")) if os.path.exists(_CID_P) else {}
CID_TAB_USO = collections.Counter()
def cid_por_tabela(chars):
    base_ = lambda n: re.sub(r"-Identity-[HV]$", "", re.sub(r"^[A-Z]{6}\+", "", n))
    alvo = []
    for c in chars:
        m_ = re.fullmatch(r"\(cid:(\d+)\)", c["text"])
        if not m_: continue
        t_ = CID_TAB.get(base_(c["fontname"]))
        if t_ is None: continue
        n_ = int(m_.group(1))
        u_ = t_.get(str(n_)) or (chr(n_ + 29) if 3 <= n_ <= 97 else None)
        if u_: alvo.append((c, u_))
    if len(alvo) < 20: return
    # trava pelo vocabulario: junta os caracteres traduzidos em palavras (pela posicao) e confere
    txt_ = []; ult_ = None
    for c, u_ in sorted(alvo, key=lambda cu: (round(cu[0]["top"]), cu[0]["x0"])):
        if ult_ is not None and (abs(c["top"] - ult_["top"]) > 2 or c["x0"] - ult_["x1"] > 1.5): txt_.append(" ")
        txt_.append(u_); ult_ = c
    pals_ = [p for p in re.findall(r"[a-záéíóúâêôãõçà]{4,}", "".join(txt_).lower())]
    if not pals_ or sum(1 for p in pals_ if p in VOC) < 0.6 * len(pals_): return
    for c, u_ in alvo: c["text"] = u_
    CID_TAB_USO[PID] += len(alvo)
def palavras(page):
    page_orig = page
    page = page.dedupe_chars(tolerance=1)     # caractere impresso 2x no mesmo lugar (ex.: "CaCl2··2H2O")
    chars = [dict(c) for c in page.chars]
    cid_por_tabela(chars)                     # "(cid:N)" de Arial sem ToUnicode (ENEM 2017-2018): tabela da numeracao original
    glifos_t3(page_orig, chars)               # glifos de fonte Type3 (imagem) reconhecidos viram texto
    glifos_cid(page_orig, chars)              # "(cid:N)" de fonte sem tabela de texto: reconhecido pela forma
    # texto girado (ex.: rotulo vertical de eixo de grafico "Altura em relacao ao solo") nao e texto corrido:
    # fica fora das palavras e, como tinta, vai junto com a figura
    chars = [c for c in chars if c.get("upright", True)]
    # microtexto de seguranca ("ENEM2024ENEM2024..." a 1-2 pt entre as colunas e no pe da pagina): ilegivel, nao e prova
    chars = [c for c in chars if c.get("size", 10) >= 2.5]
    ws = WordExtractor(extra_attrs=["fontname", "size"], keep_blank_chars=False, x_tolerance=1.2, y_tolerance=2).extract_words(chars)
    # texto invisivel (camada oculta, ex.: resolucao escondida no caderno do Bernoulli; texto branco sobre branco):
    # a pagina renderizada nao tem tinta nenhuma na caixa da palavra -> nao e texto da prova
    try:
        s_v = 72 / 72
        base_v = os.path.join(TMP, f"_vis_{PID}_{os.getpid()}")
        subprocess.run(["pdftoppm", "-r", "72", "-gray", "-f", str(page_orig.page_number), "-l", str(page_orig.page_number), "-singlefile", "-png", PDF, base_v],
                       check=True, capture_output=True)
        im_v = cv2.imread(base_v + ".png", cv2.IMREAD_GRAYSCALE)
        if im_v is not None:
            inv = set()
            for k_, w in enumerate(ws):
                reg_v = im_v[max(0, int(w["top"]) - 1):int(w["bottom"]) + 2, max(0, int(w["x0"]) - 1):int(w["x1"]) + 2]
                if reg_v.size and reg_v.min() >= 245: inv.add(k_)
            # so descarta linha (quase) toda invisivel: uma palavra solta "sem tinta" costuma ser so metrica errada da fonte
            por_l = collections.defaultdict(list)
            for k_, w in enumerate(ws): por_l[round(w["top"])].append(k_)
            tirar_v = set()
            for ks in por_l.values():
                if sum(1 for k_ in ks if k_ in inv) >= 0.7 * len(ks): tirar_v |= {k_ for k_ in ks if k_ in inv}
                else:
                    # bloco oculto que continua na mesma linha de um texto visivel ("mulheres empregadas. Alternativa E"):
                    # 2+ palavras seguidas sem tinta no fim da linha
                    # (ou separadas do texto visivel por um vao de coluna: "Alternativa E" na esquerda, texto na direita)
                    ord_ = sorted(ks, key=lambda k_: ws[k_]["x0"]); corrida = []
                    def fecha(corr, prox):
                        if len(corr) < 2: return
                        ant_ = ord_.index(corr[0]) - 1
                        vao_e = ant_ < 0 or ws[corr[0]]["x0"] - ws[ord_[ant_]]["x1"] > 2 * ws[corr[0]]["size"]
                        vao_d = prox is None or ws[prox]["x0"] - ws[corr[-1]]["x1"] > 2 * ws[corr[-1]]["size"]
                        if prox is None or (vao_e and vao_d): tirar_v.update(corr)
                    for k_ in ord_:
                        if k_ in inv: corrida.append(k_)
                        else: fecha(corrida, k_); corrida = []
                    fecha(corrida, None)
            vis = [w for k_, w in enumerate(ws) if k_ not in tirar_v]
            if len(vis) < len(ws):
                INVISIVEIS[page_orig.page_number] = len(ws) - len(vis)
            ws = vis
    except Exception:
        pass
    t3f = T3_FORMULA.get(page_orig.page_number, [])
    for w in ws:
        w["bold"], w["ital"] = estilo(w["fontname"])
        if t3f:
            hit = [b for b in t3f if b[0] < w["x1"] + 0.2 and b[2] > w["x0"] - 0.2 and b[1] < w["bottom"] and b[3] > w["top"]]
            if hit: w["t3f"] = 2 if any(b[4] for b in hit) else 1
        w["sup"] = w["sub"] = False
        # fonte Symbol: letras latinas no PDF sao letras gregas na pagina (a = alfa, p = pi...)
        if "symbol" in w["fontname"].lower() and re.search(r"[A-Za-z]", w["text"]) and "(cid:" not in w["text"]:
            w["text"] = "".join(GREGO.get(ch, ch) for ch in w["text"])
        # fonte Symbol com os codigos na area privada do Unicode (U+F02B = "+", U+F0DE = "⇒"): converte pela tabela da Symbol
        if "symbol" in w["fontname"].lower() and re.search("[\uf020-\uf0ff]", w["text"]):
            w["text"] = "".join(SYMBOL_PUA.get(ord(ch) - 0xF000, ch) if 0xF020 <= ord(ch) <= 0xF0FF else ch for ch in w["text"])
    # versalete ("TEXTO" escrito com o T maior e "EXTO" menor): o PDF separa em duas palavras por mudar o tamanho.
    # Letras maiusculas coladas, na mesma linha de base e na mesma fonte sao uma palavra so (fica o tamanho maior).
    ws.sort(key=lambda w: w["x0"])
    juntas = []; ult = {}
    for w in ws:
        a_ = None
        for k_ in (round(w["bottom"]) - 1, round(w["bottom"]), round(w["bottom"]) + 1):
            c_ = ult.get(k_)
            if (c_ is not None and abs(c_["bottom"] - w["bottom"]) < 0.8 and -0.3 <= w["x0"] - c_["x1"] < 0.5
                    and abs(c_["size"] - w["size"]) > 0.3 and c_["fontname"].split("+")[-1] == w["fontname"].split("+")[-1]
                    and re.fullmatch(r"[A-ZÀ-ÖØ-Þ]+", c_["text"]) and re.fullmatch(r"[A-ZÀ-ÖØ-Þ]+[.,;:]?", w["text"])):
                a_ = c_
        if a_ is not None:
            a_["text"] += w["text"]; a_["x1"] = w["x1"]; a_["top"] = min(a_["top"], w["top"]); a_["size"] = max(a_["size"], w["size"])
            continue
        juntas.append(w); ult[round(w["bottom"])] = w
    return juntas
# fonte Symbol (codificacao propria, 0x20-0xFF) -> Unicode; pedacos de parentese/chave grande ficam de fora (PENDENTE)
SYMBOL_PUA = dict(zip(range(0x20, 0x7F), " !∀#∃%&∋()∗+,−./0123456789:;<=>?≅ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ[∴]⊥_‾αβχδεφγηιϕκλμνοπθρστυϖωξψζ{|}∼"))
SYMBOL_PUA.update(dict(zip(range(0xA1, 0xE2), "ϒ′≤⁄∞ƒ♣♦♥♠↔←↑→↓°±″≥×∝∂•÷≠≡≈…⏐⎯↵ℵℑℜ℘⊗⊕∅∩∪⊃⊇⊄⊂⊆∈∉∠∇®©™∏√⋅¬∧∨⇔⇐⇑⇒⇓◊〈")))
SYMBOL_PUA.update({0xE5: "∑", 0xF1: "〉", 0xF2: "∫"})
GREGO = dict(zip("abgdezhqiklmnxoprstufcywABGDEZHQIKLMNXOPRSTUFCYWjJv",
                 "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩϕϑϖ"))

def tamanho_corpo(ws):
    c = collections.Counter(round(w["size"], 1) for w in ws for _ in w["text"])
    return c.most_common(1)[0][0] if c else 10

def agrupa_linhas(ws, corpo):
    """Agrupa palavras em linhas. Palavras pequenas coladas acima/abaixo viram expoente/indice."""
    # pontuacao solta (".", ",") com tamanho de fonte diferente da palavra colada: assume o tamanho da palavra
    for w in ws:
        if re.fullmatch(r"[.,;:!?)\]…]+", w["text"]):
            viz_ = [o for o in ws if o is not w and abs(o["bottom"] - w["bottom"]) < 1.5 and -1 <= w["x0"] - o["x1"] < 3 and not re.fullmatch(r"[.,;:!?)\]…]+", o["text"])]
            if viz_: w["size"] = viz_[0]["size"]
    # cabecalho de questao em letra menor que o texto ("Questão 30" a 7 pt no ENEM 1998-2012): nao e indice/expoente
    for w in ws:
        if re.fullmatch(r"(?i)quest[ãa]o", w["text"]) and "bold" in w["fontname"].lower():
            num_ = [o for o in ws if re.fullmatch(r"\d{1,3}", o["text"]) and abs(o["bottom"] - w["bottom"]) < 2.5 and 0 <= o["x0"] - w["x1"] < 2 * w["size"]]
            if num_: w["cab_peq"] = num_[0]["cab_peq"] = True
    grandes = sorted([w for w in ws if w["size"] >= 0.8 * corpo or w.get("cab_peq")], key=lambda w: (w["top"], w["x0"]))
    peq = [w for w in ws if w["size"] < 0.8 * corpo and not w.get("cab_peq")]
    linhas = []
    # letra de alternativa sozinha ao lado de uma fracao empilhada (letra na altura do traco, numerador acima dela):
    # fica na mesma linha da fracao (senao cada fracao ia para a alternativa anterior)
    def _letra_so(ws_): return len(ws_) == 1 and re.fullmatch(r"\(?[A-Ea-e][).]?|([A-E])\1", ws_[0]["text"])
    def _na_fracao(fr_, ws_):
        cx_ = fr_.get("caixa")
        if not (fr_.get("latex") and cx_ and fr_["tex"].startswith("\\frac") and _letra_so(ws_)): return False
        c_ = (ws_[0]["top"] + ws_[0]["bottom"]) / 2
        return cx_[1] < c_ < cx_[3] and 0 < fr_["x0"] - ws_[0]["x1"] < 4 * corpo
    for w in grandes:
        for l in linhas:
            # (linha "letra + fracao": o resto da linha da letra, ex. "9 ×", entra pela altura da letra)
            letra_fr_ = (len(l["ws"]) == 1 and (_na_fracao(l["ws"][0], [w]) or _na_fracao(w, l["ws"]))) or (
                2 <= len(l["ws"]) <= 4 and _na_fracao(w, [min(l["ws"], key=lambda v: v["x0"])]) and all(v["x1"] <= w["x0"] + 1 for v in l["ws"]))
            if (abs(l["top"] - w["top"]) <= 0.35 * corpo or letra_fr_ or ("top_txt" in l and abs(l["top_txt"] - w["top"]) <= 0.35 * corpo
                    and w["x1"] <= max(v["x0"] for v in l["ws"] if v.get("latex")) + 1)) \
                    and (abs(l["size"] - w["size"]) < 3 or w.get("latex") or any(v.get("latex") for v in l["ws"])):
                if letra_fr_: l["top_txt"] = (w if not w.get("latex") else l["ws"][0])["top"]
                l["ws"].append(w); l["top"] = min(l["top"], w["top"]); l["bottom"] = max(l["bottom"], w["bottom"]); break
        else:
            linhas.append({"ws": [w], "top": w["top"], "bottom": w["bottom"], "size": w["size"]})
    sobras = []
    # (varias passadas: o sinal "−" de "−1" so encosta na linha depois que o "1" do indice ja entrou nela)
    pend_ = list(peq)
    for _passada in range(3):
        sobras = []
        for w in pend_:
            melhor = None
            hw = max(0.1, w["bottom"] - w["top"])
            for l in linhas:
                ov = min(w["bottom"], l["bottom"]) - max(w["top"], l["top"])
                if ov < 0.2 * hw: continue
                viz = min(max(0, x["x0"] - w["x1"], w["x0"] - x["x1"]) for x in l["ws"])
                if viz < 2.5 and (melhor is None or viz < melhor[0]): melhor = (viz, l)
            if melhor:
                l = melhor[1]; meio = (l["top"] + l["bottom"]) / 2; cw = (w["top"] + w["bottom"]) / 2
                if cw < meio - 0.1 * l["size"]: w["sup"] = True
                elif cw > meio + 0.1 * l["size"]: w["sub"] = True
                l["ws"].append(w)
            else:
                sobras.append(w)
        if len(sobras) == len(pend_): break
        pend_ = sobras
    peq = []
    for w in peq:
        melhor = None
        hw = max(0.1, w["bottom"] - w["top"])
        for l in linhas:
            ov = min(w["bottom"], l["bottom"]) - max(w["top"], l["top"])
            if ov < 0.2 * hw: continue
            viz = min(max(0, x["x0"] - w["x1"], w["x0"] - x["x1"]) for x in l["ws"])
            if viz < 2.5 and (melhor is None or viz < melhor[0]): melhor = (viz, l)
        if melhor:
            l = melhor[1]; meio = (l["top"] + l["bottom"]) / 2; cw = (w["top"] + w["bottom"]) / 2
            if cw < meio - 0.1 * l["size"]: w["sup"] = True
            elif cw > meio + 0.1 * l["size"]: w["sub"] = True
            l["ws"].append(w)
        else:
            sobras.append(w)
    # palavras pequenas soltas formam linhas proprias (fonte/citacao, notas)
    for w in sorted(sobras, key=lambda w: (-w["size"], w["top"], w["x0"])):
        hw = max(0.1, w["bottom"] - w["top"])
        for l in linhas:
            if l.get("pequena") and min(w["bottom"], l["bottom"]) - max(w["top"], l["top"]) >= 0.3 * hw:
                if w["size"] < 0.8 * l["size"]:
                    meio = (l["top"] + l["bottom"]) / 2; cw = (w["top"] + w["bottom"]) / 2
                    if cw < meio - 0.1 * l["size"]: w["sup"] = True
                    elif cw > meio + 0.1 * l["size"]: w["sub"] = True
                l["ws"].append(w); break
        else:
            linhas.append({"ws": [w], "top": w["top"], "bottom": w["bottom"], "size": w["size"], "pequena": True})
    final = []
    for l in linhas:    # separa pedacos da mesma altura muito distantes (rotulos de figura, celulas)
        l["ws"].sort(key=lambda w: w["x0"])
        grupo = [l["ws"][0]]
        for w in l["ws"][1:]:
            if w["x0"] - grupo[-1]["x1"] > 2.5 * corpo and not (w["sup"] or w["sub"]):
                final.append({**l, "ws": grupo}); grupo = [w]
            else: grupo.append(w)
        final.append({**l, "ws": grupo})
    for l in final:
        l["x0"] = min(w["x0"] for w in l["ws"]); l["x1"] = max(w["x1"] for w in l["ws"])
        l["top"] = min(w["top"] for w in l["ws"] if not w["sup"] and not w["sub"]) if any(not w["sup"] and not w["sub"] for w in l["ws"]) else l["top"]
    return sorted(final, key=lambda l: (l["top"], l["x0"]))

def md_linha(l):
    """Texto da linha em Markdown, preservando negrito, italico, expoente e indice."""
    out = []; prev = None
    for w in l["ws"]:
        t = w["text"]
        if w["sup"]: t = f"<sup>{t}</sup>"
        elif w["sub"]: t = f"<sub>{t}</sub>"
        if prev is not None:
            gap = w["x0"] - prev["x1"]
            colado = ((re.match(r"^[)\]]", w["text"]) or re.search(r"[(\[]$", prev["text"])) and gap < 0.3 * max(prev["size"], w["size"])) or \
                     (re.match(r"^[,.]", w["text"]) and gap < 0.2 * max(prev["size"], w["size"]))
            if (gap > 0.12 * max(prev["size"], w["size"]) and not (w["sup"] or w["sub"]) or (gap > 1.5)) and not colado:
                out.append(" ")
        out.append((t, w["bold"], w["ital"], bool(w.get("subl")))); prev = w
    # junta runs de mesmo estilo
    res = []; run = []; cur = None
    def fecha():
        if not run: return
        s = "".join(run); b, i, u = cur
        lead = len(s) - len(s.lstrip()); trail = len(s) - len(s.rstrip()); core = s.strip()
        if core and b and i: core = f"***{core}***"
        elif core and b: core = f"**{core}**"
        elif core and i: core = f"*{core}*"
        if core and u: core = f"<u>{core}</u>"
        res.append(" " * lead + core + " " * trail)
    for x in out:
        if isinstance(x, str): run.append(x); continue
        t, b, i, u = x
        if cur is not None and (b, i, u) != cur: fecha(); run = []
        cur = (b, i, u); run.append(t)
    fecha()
    return "".join(res)

def txt_puro(l): return " ".join(w["text"] for w in l["ws"])
def mesma_col_(a, b): return a.get("pg") == b.get("pg") and abs(a["col"][0] - b["col"][0]) < 1
def fim_frase_prev_ok(prev): return re.search(r"[.:!?”\"»)]$", txt_puro(prev)) is not None

# ------------------------------------------------------------------ cabecalho/rodape repetidos
def norm(s): return re.sub(r"\d+", "#", s.strip().lower())
def fracoes(page, ws):
    """Matematica desenhada vira texto LaTeX (entre \( \)), so quando da para ter certeza:
    1) raiz: sinal grafico de raiz cobrindo letras -> \sqrt{...}
    2) fracao empilhada: numerador / traco / denominador -> \frac{..}{..}
    3) tracinho ou arco sobre letras -> \widehat{..}; seta sobre letras -> \overrightarrow{..}
    Se houver outro grafico no meio (algo que o codigo nao entende), nada e convertido e o trecho vira imagem."""
    ws = list(ws); usadas = set(); novas = []; graf_usados = set()
    objs = [dict(o, _k=k) for k, o in enumerate(page.lines + page.rects + page.curves + BARRAS_T3.get(page.page_number, []))]
    def TEX(w): return w["tex"] if w.get("tex") else w["text"].replace("\\", "\\backslash ").replace("{", "\\{").replace("}", "\\}").replace("%", "\\%").replace("$", "\\$").replace("#", "\\#").replace("&", "\\&").replace("_", "\\_")
    def tex(grupo):
        grupo = sorted(grupo, key=lambda w: w["x0"])
        # parentese/colchete grande (maior que os numeros) nao define o tamanho normal: senao "(6 − 2)!" vira indice
        mx = max([w["size"] for w in grupo if not re.fullmatch(r"[()\[\]{}|]+", w["text"])] or [w["size"] for w in grupo])
        base = [w for w in grupo if w["size"] >= 0.8 * mx]
        ref = (min(w["top"] for w in base) + max(w["bottom"] for w in base)) / 2 if base else 0
        out = ""; prev = None
        for w in grupo:
            t = TEX(w)
            if w["size"] < 0.8 * mx and not w.get("tex"):
                c = (w["top"] + w["bottom"]) / 2
                t = ("^{%s}" if c < ref else "_{%s}") % t
            elif prev is not None and w["x0"] - prev > 1.2:
                t = "\\," + t
            out += t; prev = w["x1"]
        return out
    def nova(raw, x0, top, x1, bottom, ref, caixa):
        return {"text": "\\(" + raw + "\\)", "tex": raw, "x0": x0, "x1": x1, "top": top, "bottom": bottom,
                "fontname": ref["fontname"], "size": ref["size"], "bold": False, "ital": False, "sup": False, "sub": False,
                "latex": True, "caixa": caixa}
    def livres(): return [w for k, w in enumerate(ws) if k not in usadas]
    def intersecta(bb, excluir):
        return [o for o in objs if o["_k"] not in excluir and o["_k"] not in graf_usados and
                min(o["x1"], bb[2]) - max(o["x0"], bb[0]) > 0.5 and min(o["bottom"], bb[3]) - max(o["top"], bb[1]) > 0.5]
    # sublinhado: traco fino logo abaixo da palavra (sem nada embaixo) -> a palavra fica marcada como sublinhada
    for o in objs:
        if o["_k"] in graf_usados or (o["bottom"] - o["top"]) > 1.3 or (o["x1"] - o["x0"]) < 3: continue
        sob = [w for w in ws if w["top"] < o["top"] and o["top"] - 2.5 <= w["bottom"] <= o["top"] + 2.0
               and min(w["x1"], o["x1"]) - max(w["x0"], o["x0"]) > 0.8 * (w["x1"] - w["x0"])]
        if not sob: continue
        # borda de tabela/moldura nao e sublinhado: tem traco vertical encostando na ponta
        grade_ = [v for v in objs if v is not o and (v["bottom"] - v["top"]) > 4 and (v["x1"] - v["x0"]) < 2.5
                  and v["top"] - 1.5 <= o["top"] <= v["bottom"] + 1.5 and (abs(v["x0"] - o["x0"]) < 2 or abs(v["x1"] - o["x1"]) < 2)]
        if grade_ or any(o["top"] - w["bottom"] > 1.2 for w in sob): continue
        # a palavra de cima esta numa linha de texto comum (tem vizinhas na mesma altura fora do traco)
        linha_cima = [w for w in ws if abs(w["top"] - sob[0]["top"]) < 1.5 and (w["x1"] < o["x0"] - 1 or w["x0"] > o["x1"] + 1)]
        # embaixo: denominador (palavras so dentro do traco) = fracao; linha de texto que passa das pontas = sublinhado
        perto_baixo = [w for w in ws if -1 <= w["top"] - o["bottom"] <= 6.5]
        dentro_b = [w for w in perto_baixo if w["x0"] >= o["x0"] - 2 and w["x1"] <= o["x1"] + 2]
        passa = [w for w in perto_baixo if (w["x0"] < o["x0"] - 1 < w["x1"]) or (w["x0"] < o["x1"] + 1 < w["x1"])]
        if not linha_cima or (dentro_b and not passa): continue
        if (o["x1"] - o["x0"]) > 1.3 * (max(w["x1"] for w in sob) - min(w["x0"] for w in sob)) + 4: continue
        graf_usados.add(o["_k"])
        for w in sob:
            w["subl"] = True
            bx = w.get("caixa") or (w["x0"], w["top"], w["x1"], w["bottom"])
            w["caixa"] = (bx[0], bx[1], bx[2], max(bx[3], o["bottom"] + 0.5))
    # 0) seta de reacao quimica no meio da linha ("R3N + HCl ---> (R3NH)+Cl-"): vira o caractere da seta
    #    (-> , <- , <-> ou o duplo de equilibrio), para a equacao ficar como texto e a seta nao sumir
    horiz = [o for o in objs if (o["bottom"] - o["top"]) <= 1.6 and 8 <= (o["x1"] - o["x0"]) <= 90 and not o.get("so_sobrelinha")]
    pontas = [p for p in objs if p.get("fill") and (p["x1"] - p["x0"]) < 10 and (p["bottom"] - p["top"]) < 10]
    for o in horiz:
        if o["_k"] in graf_usados: continue
        y = (o["top"] + o["bottom"]) / 2
        na_linha = [w for w in livres() if abs((w["top"] + w["bottom"]) / 2 - y) < 0.45 * w["size"] + 1.5 and not w["sup"] and not w["sub"]]
        esq = [w for w in na_linha if o["x0"] - 25 <= w["x1"] <= o["x0"] + 3]
        dir_ = [w for w in na_linha if o["x1"] - 3 <= w["x0"] <= o["x1"] + 25]
        if not esq or not dir_: continue
        if any(w["x1"] > o["x0"] + 3 and w["x0"] < o["x1"] - 3 for w in na_linha): continue
        par_ = [p for p in horiz if p is not o and p["_k"] not in graf_usados and 1 <= abs((p["top"] + p["bottom"]) / 2 - y) <= 5
                and min(p["x1"], o["x1"]) - max(p["x0"], o["x0"]) > 0.6 * (o["x1"] - o["x0"])]
        def ponta_em(lin, x):
            yy = (lin["top"] + lin["bottom"]) / 2
            return [p for p in pontas if p["_k"] not in graf_usados and abs((p["top"] + p["bottom"]) / 2 - yy) < 4 and (p["x0"] - 3 <= x <= p["x1"] + 3)]
        pd_, pe_ = ponta_em(o, o["x1"]), ponta_em(o, o["x0"])
        usados_o = [o] + pd_ + pe_
        if par_:
            q_ = par_[0]; usados_o += [q_] + ponta_em(q_, q_["x1"]) + ponta_em(q_, q_["x0"])
            simb = "\u21cc"          # equilibrio
        elif pd_ and pe_: simb = "\u2194"
        elif pd_: simb = "\u2192"
        elif pe_: simb = "\u2190"
        else: continue                # sem ponta: nao da para ter certeza que e seta
        for u in usados_o: graf_usados.add(u["_k"])
        x0_ = min(u["x0"] for u in usados_o); x1_ = max(u["x1"] for u in usados_o)
        y0_ = min(u["top"] for u in usados_o); y1_ = max(u["bottom"] for u in usados_o)
        ref = esq[-1]
        ws.append({"text": simb, "x0": x0_, "x1": x1_, "top": ref["top"], "bottom": ref["bottom"], "fontname": ref["fontname"],
                   "size": ref["size"], "bold": False, "ital": False, "sup": False, "sub": False, "caixa": (x0_, y0_ - 0.5, x1_, y1_ + 0.5)})
    # 1) raizes
    for o in objs:
        if o["_k"] in graf_usados: continue 
        if o.get("so_sobrelinha"): continue      # sobrelinha de segmento (glifo Type3): nunca raiz/fracao
        h = o["bottom"] - o["top"]; L = o["x1"] - o["x0"]
        if not (0.6 * CORPO_PROV <= h <= 3 * CORPO_PROV and L >= 6): continue
        pts = o.get("pts") or []
        topo = [p[0] for p in pts if abs(p[1] - o["top"]) < 1.2]
        if not topo or max(topo) - min(topo) < 0.45 * L: continue          # precisa do traco de cima
        # formato de raiz: o ponto mais baixo (o "V") fica so no comeco, a esquerda; embaixo nao ha traco ate a direita
        # (moldura, borda de celula ou sublinhado nao sao raiz)
        baixo = [p[0] for p in pts if abs(p[1] - o["bottom"]) < 1.2]
        if not baixo or max(baixo) > o["x0"] + 0.6 * h + 3: continue
        if o.get("object_type") == "rect": continue
        gancho = o["x0"] + 0.3 * h
        dentro = [w for w in livres() if w["x0"] >= gancho - 1 and w["x1"] <= o["x1"] + 2 and w["top"] >= o["top"] - 1 and w["bottom"] <= o["bottom"] + 0.4 * w["size"]]
        no_gancho = [w for w in livres() if w["x1"] > o["x0"] + 1.5 and w["x0"] < gancho - 1 and w["top"] >= o["top"] - 1 and w["bottom"] <= o["bottom"] + 0.4 * w["size"]]
        # indice da raiz (raiz cubica "∛"): numero pequeno em cima do gancho, na metade de cima do sinal
        indice = [w for w in no_gancho if re.fullmatch(r"\d{1,2}|n", w["text"]) and w["size"] < 0.8 * CORPO_PROV
                  and w["top"] <= o["top"] + 0.4 * h and w["bottom"] <= o["top"] + 0.8 * h and w not in dentro]
        if len(indice) == 1 and len(no_gancho) == 1: no_gancho = []
        else: indice = []
        if not dentro or no_gancho: continue
        graf_usados.add(o["_k"])
        for w in dentro + indice: usadas.add(ws.index(w))
        w0 = max(dentro, key=lambda w: w["size"])
        ws.append(nova(("\\sqrt[%s]{%s}" % (indice[0]["text"], tex(dentro))) if indice else "\\sqrt{%s}" % tex(dentro),
                       min([o["x0"]] + [w["x0"] for w in indice]), min(w["top"] for w in dentro), o["x1"], max(w["bottom"] for w in dentro), w0,
                       (min([o["x0"]] + [w["x0"] for w in indice]), min([o["top"]] + [w["top"] for w in indice]), o["x1"], o["bottom"])))
    # 2) fracoes
    for o in objs:
        if o["_k"] in graf_usados: continue 
        if o.get("so_sobrelinha"): continue      # sobrelinha de segmento (glifo Type3): nunca raiz/fracao
        h = o["bottom"] - o["top"]; L = o["x1"] - o["x0"]
        if not (h <= 1.6 and 3 <= L <= 90): continue
        b = (o["x0"], o["top"], o["x1"], o["bottom"]); cyb = (b[1] + b[3]) / 2; cx = (b[0] + b[2]) / 2
        # traco que faz parte de grade de tabela (continua de lado ou tem linha vertical na ponta) nao e fracao
        grade = [x for x in objs if x["_k"] != o["_k"] and (
                 ((x["bottom"] - x["top"]) > 3 and (x["x1"] - x["x0"]) < 2.5 and x["top"] - 2 <= cyb <= x["bottom"] + 2 and
                  (abs(x["x0"] - b[0]) < 2.5 or abs(x["x1"] - b[2]) < 2.5)) or
                 ((x["bottom"] - x["top"]) <= 1.6 and abs((x["top"] + x["bottom"]) / 2 - cyb) < 1 and (abs(x["x0"] - b[2]) < 2 or abs(x["x1"] - b[0]) < 2)))]
        if grade: continue
        ac = [w for w in livres() if (w["top"] + w["bottom"]) / 2 < cyb and -3 <= b[1] - w["bottom"] <= 7 and w["x0"] >= b[0] - 2 and w["x1"] <= b[2] + 2]
        ab = [w for w in livres() if (w["top"] + w["bottom"]) / 2 > cyb and -3 <= w["top"] - b[3] <= 7 and w["x0"] >= b[0] - 2 and w["x1"] <= b[2] + 2]
        if ac: ac += [w for w in livres() if w not in ac and w["size"] < 0.8 * CORPO_PROV and (w["top"] + w["bottom"]) / 2 < cyb and b[1] - w["bottom"] <= 10 and w["x0"] >= b[0] - 2 and w["x1"] <= b[2] + 3]
        if ab: ab += [w for w in livres() if w not in ab and w["size"] < 0.8 * CORPO_PROV and (w["top"] + w["bottom"]) / 2 > cyb and w["top"] - b[3] <= 11 and w["x0"] >= b[0] - 2 and w["x1"] <= b[2] + 3]
        if not ac or not ab: continue
        def centro(g): return (min(w["x0"] for w in g) + max(w["x1"] for w in g)) / 2
        def larg(g): return max(w["x1"] for w in g) - min(w["x0"] for w in g)
        if abs(centro(ac) - cx) > 0.3 * L or abs(centro(ab) - cx) > 0.3 * L: continue
        if L > 1.6 * max(larg(ac), larg(ab)) + 6: continue
        caixa = (b[0], min(w["top"] for w in ac), b[2], max(w["bottom"] for w in ab))
        outros = [x for x in intersecta(caixa, {o["_k"]}) if (x["x1"] - x["x0"]) > 1.5 or (x["bottom"] - x["top"]) > 1.5]
        if outros: continue                       # tem grafico que nao e o traco: nao converte
        graf_usados.add(o["_k"])
        for w in ac + ab: usadas.add(ws.index(w))
        ws.append(nova("\\frac{%s}{%s}" % (tex(ac), tex(ab)), b[0], cyb - 0.55 * CORPO_PROV, b[2], cyb + 0.45 * CORPO_PROV, ab[0], caixa))
    # 3) chapeu / seta sobre letras
    for o in objs:
        if o["_k"] in graf_usados: continue
        h = o["bottom"] - o["top"]; L = o["x1"] - o["x0"]
        if not (h <= 4.5 and 3 <= L <= 40): continue
        sob = [w for w in livres() if -1 <= w["top"] - o["bottom"] <= 3 and w["x1"] > o["x0"] and w["x0"] < o["x1"]]
        if not sob: continue
        eh_curva = o.get("object_type") == "curve"
        acima = [w for w in livres() if -0.5 <= o["top"] - w["bottom"] <= 3 and w["x1"] > o["x0"] and w["x0"] < o["x1"]]
        tem_ponta = any(p["_k"] != o["_k"] and p.get("fill") and (p["x1"] - p["x0"]) < 6 and (p["bottom"] - p["top"]) < 6
                        and abs((p["top"] + p["bottom"]) / 2 - (o["top"] + o["bottom"]) / 2) < 3 and (abs(p["x1"] - o["x1"]) < 4 or abs(p["x0"] - o["x0"]) < 4) for p in objs)
        if acima and not eh_curva and not tem_ponta: continue
        larg_sob = max(w["x1"] for w in sob) - min(w["x0"] for w in sob)
        if L > 1.3 * larg_sob + 3: continue
        if L < 0.3 * larg_sob: continue          # tracinho minusculo sobre palavra longa (enfeite/sublinhado de outra coisa)
        verticais = [v for v in page.lines + page.rects if (v["bottom"] - v["top"]) > 4 and (v["x1"] - v["x0"]) < 2 and
                     v["top"] - 1 <= o["top"] <= v["bottom"] + 1 and (abs(v["x0"] - o["x0"]) < 1.5 or abs(v["x1"] - o["x1"]) < 1.5)]
        if verticais: continue
        mx = max(w["size"] for w in sob)
        xa, xb = min(w["x0"] for w in sob), max(w["x1"] for w in sob)
        sob += [w for w in livres() if w not in sob and w["size"] < 0.8 * mx and xa - 1 <= w["x0"] and w["x1"] <= xb + 4
                and w["top"] < max(x["bottom"] for x in sob) + 2 and w["bottom"] > min(x["top"] for x in sob)]
        # seta: ponta preenchida perto de uma das extremidades
        ponta = [p for p in objs if p["_k"] != o["_k"] and p.get("fill") and (p["x1"] - p["x0"]) < 6 and (p["bottom"] - p["top"]) < 6
                 and abs((p["top"] + p["bottom"]) / 2 - (o["top"] + o["bottom"]) / 2) < 3 and (abs(p["x1"] - o["x1"]) < 4 or abs(p["x0"] - o["x0"]) < 4)]
        # arco (chapeu de angulo): as duas pontas ficam embaixo; seta: as pontas ficam na altura do meio
        pts_o = o.get("pts") or []
        arco = False
        if len(pts_o) >= 3:
            px0 = min(pts_o, key=lambda p: p[0]); px1 = max(pts_o, key=lambda p: p[0])
            arco = px0[1] > o["top"] + 0.6 * h and px1[1] > o["top"] + 0.6 * h
        seta = bool(ponta) or (o.get("fill") and eh_curva and h >= 1.5 and not arco)
        graf_usados.add(o["_k"]); [graf_usados.add(p["_k"]) for p in ponta]
        for w in sob: usadas.add(ws.index(w))
        principal = [w for w in sob if w["size"] >= 0.8 * mx]
        cmd = "\\overrightarrow" if seta else "\\widehat" if (arco or eh_curva) else "\\overline"   # traco reto = sobrelinha (segmento)
        ws.append(nova("%s{%s}" % (cmd, tex(sob)), xa, min(w["top"] for w in principal), xb, max(w["bottom"] for w in principal), principal[0],
                       (min(o["x0"], xa) - 1, o["top"] - 1.5, max(o["x1"], xb) + 1, max(w["bottom"] for w in sob))))
    return [w for k, w in enumerate(ws) if k not in usadas]

paginas = []
for i, page in enumerate(pdf.pages):
    ws = palavras(page)
    paginas.append({"n": i + 1, "page": page, "ws": ws})
_c = collections.Counter()
for pg in paginas:
    for w in pg["ws"]: _c[round(w["size"], 1)] += len(w["text"])
CORPO_PROV = _c.most_common(1)[0][0] if _c else 10
NFRAC = 0
for pg in paginas:
    antes = len(pg["ws"]); pg["ws"] = fracoes(pg["page"], pg["ws"]); NFRAC += sum(1 for w in pg["ws"] if w.get("latex"))
corpo_global = collections.Counter()
for pg in paginas:
    for w in pg["ws"]: corpo_global[round(w["size"], 1)] += len(w["text"])
CORPO = corpo_global.most_common(1)[0][0]
def regioes(ws, W, H, page=None):
    """Divide a pagina em faixas horizontais: faixa de largura total (texto atravessa o meio) ou faixa com 2 colunas.
    Devolve lista de (x0, x1, y0, y1) na ordem de leitura."""
    meio = W / 2
    corpo = [w for w in ws if w["size"] >= 0.8 * CORPO and 0.06 * H < w["top"] < 0.95 * H]
    todos = [w for w in ws if w["size"] >= 0.6 * CORPO and 0.06 * H < w["top"] < 0.95 * H]
    cruz = [[w["top"] - 2, w["bottom"] + 2] for w in todos if w["x0"] < meio - 3 and w["x1"] > meio + 3]
    # tambem conta como "atravessa" duas palavras vizinhas na mesma linha, uma de cada lado do meio, com espaco normal
    esq_m = [w for w in corpo if w["x1"] <= meio + 3]; dir_m = [w for w in corpo if w["x0"] >= meio - 3]
    for a in esq_m:
        for b in dir_m:
            if abs(a["top"] - b["top"]) < 2 and 0 <= b["x0"] - a["x1"] < 0.7 * a["size"] and abs(a["size"] - b["size"]) < 0.5:
                cruz.append([min(a["top"], b["top"]) - 2, max(a["bottom"], b["bottom"]) + 2])
    cruz.sort()
    faixas = []
    for a, b in cruz:
        a, b = a - 0.2 * CORPO, b + 0.35 * CORPO
        if faixas and a <= faixas[-1][1] + 1.5 * CORPO: faixas[-1][1] = max(faixas[-1][1], b)
        else: faixas.append([a, b])
    graf = []
    if page is not None:
        for o in page.rects + page.curves + page.images + page.lines:
            x0, t, x1, b = o["x0"], o["top"], o["x1"], o["bottom"]
            if (x1 - x0) > 5 and (b - t) > 5 and (b - t) < 0.8 * H and 0.06 * H < t < 0.95 * H:
                graf.append((max(0, x0), t, min(W, x1), b))
    # desenho largo que atravessa o meio da pagina (figura de largura total entre o texto-base e as colunas, como a
    # cerca da UNICAMP 2012): a faixa dele e de largura total, para a figura ficar na ordem de leitura certa
    if graf and len(graf) <= 1500:
        grp = [list(g) for g in graf]
        mud_g = True
        while mud_g:
            mud_g = False
            for i_ in range(len(grp)):
                for j_ in range(i_ + 1, len(grp)):
                    A_, B_ = grp[i_], grp[j_]
                    if A_[0] - 3 <= B_[2] and B_[0] - 3 <= A_[2] and A_[1] - 3 <= B_[3] and B_[1] - 3 <= A_[3]:
                        grp[i_] = [min(A_[0], B_[0]), min(A_[1], B_[1]), max(A_[2], B_[2]), max(A_[3], B_[3])]
                        grp.pop(j_); mud_g = True; break
                if mud_g: break
        for g in grp:
            if g[0] < meio - 0.15 * W and g[2] > meio + 0.15 * W and (g[3] - g[1]) > 2 * CORPO and (g[3] - g[1]) < 0.6 * H:
                dentro_w = [w for w in corpo if g[0] <= w["x0"] and w["x1"] <= g[2] and g[1] <= w["top"] and w["bottom"] <= g[3]]
                if len(dentro_w) <= 8:
                    a_, b_ = g[1] - 0.2 * CORPO, g[3] + 0.35 * CORPO
                    sobre = [f_ for f_ in faixas if f_[0] <= b_ + 1.5 * CORPO and a_ <= f_[1] + 1.5 * CORPO]
                    for f_ in sobre: faixas.remove(f_); a_, b_ = min(a_, f_[0]), max(b_, f_[1])
                    faixas.append([a_, b_]); faixas.sort()
    regs = []; y = 0
    def duas(y0, y1):
        esq = [w for w in corpo if y0 <= w["top"] < y1 and w["x1"] <= meio + 3]
        dir_ = [w for w in corpo if y0 <= w["top"] < y1 and w["x0"] >= meio - 3]
        ini_dir = {round(w["top"]) for w in dir_ if w["x0"] < meio + 0.08 * W}
        if len(esq) >= 3 and len(dir_) >= 3 and len(ini_dir) >= 3:
            fim_e = max(w["bottom"] for w in esq); fim_d = max(w["bottom"] for w in dir_)
            for o in graf:
                if o[1] >= y0 - 2 and o[3] <= y1 + 2:
                    if o[2] <= meio + 3: fim_e = max(fim_e, o[3])
                    elif o[0] >= meio - 3: fim_d = max(fim_d, o[3])
            corte_y = min(fim_e, fim_d) + 0.6 * CORPO
            # o lado mais longo continua depois do fim do outro: se houver um "buraco" ali, o que vem depois e outra faixa
            lado = [w for w in todos if y0 <= w["top"] < y1 and ((w["x1"] <= meio + 3) if fim_e > fim_d else (w["x0"] >= meio - 3))]
            itens_lado = [(w["top"], w["bottom"]) for w in lado] + [(o[1], o[3]) for o in graf if o[1] >= y0 - 2 and o[3] <= y1 + 2 and
                          ((o[2] <= meio + 3) if fim_e > fim_d else (o[0] >= meio - 3))]
            acima = [b_ for t_, b_ in itens_lado if t_ < corte_y]; abaixo = [t_ for t_, b_ in itens_lado if t_ >= corte_y]
            buraco = (min(abaixo) - max(acima)) if acima and abaixo else 0
            if max(fim_e, fim_d) > corte_y + CORPO and corte_y < y1 and buraco >= 1.5 * CORPO and y1 < 0.93 * H:
                regs.append((0, meio, y0, corte_y)); regs.append((meio, W, y0, corte_y))
                duas(corte_y, y1)
                return
            regs.append((0, meio, y0, y1)); regs.append((meio, W, y0, y1))
        elif esq or dir_:
            regs.append((0, W, y0, y1))
    for a, b in faixas:
        if a > y: duas(y, a)
        regs.append((0, W, a, b)); y = b
    if y < H: duas(y, H + 1)
    return regs or [(0, W, 0, H + 1)]
for pg in paginas:
    W, H = pg["page"].width, pg["page"].height
    pg["regs"] = regioes(pg["ws"], W, H, pg["page"])
    # protecao: nenhuma faixa da pagina pode ficar sem regiao (senao o texto dali some sem aviso)
    faixas_r = sorted({(r[2], r[3]) for r in pg["regs"]})
    buracos = []; y_ant = 0
    for y0_, y1_ in faixas_r:
        if y0_ > y_ant + 0.01: buracos.append((0, W, y_ant, y0_))
        y_ant = max(y_ant, y1_)
    if y_ant < H + 1: buracos.append((0, W, y_ant, H + 1))
    if buracos:
        pg["regs"] = sorted(pg["regs"] + buracos, key=lambda r: (r[2], r[0]))
    pg["linhas"] = []
    if os.environ.get("DEBUGTXT"):
        for w in pg["ws"]:
            if re.search(os.environ["DEBUGTXT"], w["text"]): print("DBGW", pg["n"], w["text"], round(w["x0"]), round(w["top"]), w["size"], pg["regs"])
    for ri, r in enumerate(pg["regs"]):
        sub = [w for w in pg["ws"] if r[0] <= (w["x0"] + w["x1"]) / 2 < r[1] and r[2] <= (w["top"] + w["bottom"]) / 2 < r[3]]
        for l in agrupa_linhas(sub, CORPO):
            l["col"] = (r[0], r[1]); l["reg"] = ri; l["pg"] = pg["n"]; pg["linhas"].append(l)
RE_CAB_Q = re.compile(r"^(?i:quest[ãa]o)\s*\d")
def chave_rep(l):
    return (frozenset(re.sub(r"\d+", "", w["text"]) for w in l["ws"]) - {""}, round(l["top"] / 10))
rep = collections.Counter()
for pg in paginas:
    for t in {chave_rep(l) for l in pg["linhas"]}: rep[t] += 1
def extremo(l, H): return l["top"] < 0.09 * H or l["bottom"] > 0.93 * H
RE_RODAPE_AREA = re.compile(r"\d\s*[º°o]\s*DIA\s*•\s*CADERNO\s+\d+|•\s*CADERNO\s+\d+\s*•")
RE_SLUG = re.compile(r"\S\.ind[db]\b")
voc_rodape = set()
for (ws_, y), c in rep.items():
    if c >= max(3, 0.25 * NPAG) and (y * 10 < 0.09 * paginas[0]["page"].height or y * 10 > 0.93 * paginas[0]["page"].height): voc_rodape |= ws_
# palavras exatas (com digitos) dos cabecalhos/rodapes repetidos, na altura em que aparecem: pedaco do cabecalho que
# caiu em outra coluna numa pagina ("ENEM" na coluna da esquerda, "2005" na da direita) tambem e cabecalho
_rep_bruto = collections.Counter()
for pg in paginas:
    for l in pg["linhas"]:
        if len(l["ws"]) >= 2: _rep_bruto[(tuple(w["text"] for w in l["ws"]), round(l["top"] / 10))] += 1
POS_RODAPE = {(t_, y) for (ts_, y), c in _rep_bruto.items() if c >= max(3, 0.25 * NPAG)
              and (y * 10 < 0.09 * paginas[0]["page"].height or y * 10 > 0.93 * paginas[0]["page"].height) for t_ in ts_ if len(t_) >= 3}
def pedaco_rodape(l):
    y = round(l["top"] / 10)
    return all(any((w["text"], y + d) in POS_RODAPE for d in (-1, 0, 1)) for w in l["ws"])
# numero sozinho no alto/pe da pagina: e numero de pagina so se acompanha a pagina (numero - pagina = constante em
# varias paginas). Numero que nao acompanha (ex.: "01" em negrito no alto = numero da questao na FUVEST) fica.
_offs = collections.Counter(int(txt_puro(l).strip()) - pg["n"] for pg in paginas for l in pg["linhas"]
                            if extremo(l, pg["page"].height) and re.fullmatch(r"\d{1,3}", txt_puro(l).strip()))
OFF_PAG = {o for o, c in _offs.items() if c >= 3}
def num_pagina(l, pg):
    t = txt_puro(l).strip()
    if not re.fullmatch(r"\d{1,3}", t): return False
    if int(t) - pg["n"] in OFF_PAG: return True
    return not (all(w["bold"] for w in l["ws"]) and l["size"] >= 0.85 * CORPO_PROV)
if os.environ.get("DEBUGCAB"):
    for pg in paginas:
        for l in pg["linhas"]:
            if extremo(l, pg["page"].height) and re.search(os.environ["DEBUGCAB"], txt_puro(l)):
                print("CAB-REP", pg["n"], txt_puro(l)[:50], rep[chave_rep(l)], chave_rep(l), bool(chave_rep(l)[0] and chave_rep(l)[0] <= voc_rodape))
for pg in paginas:
    H = pg["page"].height
    _fx = [(l["top"], l["bottom"]) for l in pg["linhas"] if extremo(l, H) and RE_RODAPE_AREA.search(txt_puro(l))]
    # rotulo de texto ("TEXTO PARA AS QUESTOES DE 07 A 09") no alto da pagina e conteudo, nunca cabecalho repetido
    # rodape/cabecalho que se repete em metade das paginas, um pouco mais para dentro (ex.: "PROVA 1 - AMARELA - 3" a 88%)
    pg["linhas"] = [l for l in pg["linhas"] if not (chave_rep(l)[0] and rep[chave_rep(l)] >= max(3, 0.5 * NPAG)
                                                    and (l["top"] < 0.13 * H or l["bottom"] > 0.87 * H) and not RE_CAB_Q.match(txt_puro(l)))]
    pg["linhas"] = [l for l in pg["linhas"] if RE_CAB_Q.match(txt_puro(l)) or RE_TEXTO_PARA.match(txt_puro(l)) or not (extremo(l, H) and (
        (rep[chave_rep(l)] >= max(3, 0.25 * NPAG) and (chave_rep(l)[0] or len(l["ws"]) > 1 or len(txt_puro(l).strip()) > 3)) or num_pagina(l, pg)
        or (chave_rep(l)[0] and chave_rep(l)[0] <= voc_rodape) or pedaco_rodape(l)))]
    # rodape do ENEM que muda com a area ("CIÊNCIAS HUMANAS E SUAS TECNOLOGIAS • 1º DIA • CADERNO 2 • AMARELO") e
    # e partido pelas colunas: a faixa inteira sai quando um pedaco tem "Nº DIA • CADERNO". Carimbo da grafica
    # ("P1_1_Dia_LCT_REG_2_Amarelo.indd 5", "...indb 321") no pe/alto da pagina sai sempre.
    pg["linhas"] = [l for l in pg["linhas"] if not (extremo(l, H) and (RE_SLUG.search(txt_puro(l))
                    or any(l["top"] < b + 2 and l["bottom"] > t - 2 for t, b in _fx)))]
    # tirinha/quadrinho em imagem embutida com o texto dos baloes numa fonte que o resto da pagina nao usa (Comic Sans):
    # o texto dos baloes e da figura (fica na imagem, nao vira texto nem parte a figura em duas). Texto escondido
    # debaixo da imagem ("QUESTAO 06" coberto pela tirinha) sai junto.
    _fam = lambda w: re.sub(r"^[A-Z]{6}\+", "", w["fontname"]).split("-")[0].split(",")[0]
    for im_ in pg["page"].images:
        bx_ = (im_["x0"], im_["top"], im_["x1"], im_["bottom"])
        den_ = [w for w in pg["ws"] if bx_[0] <= (w["x0"] + w["x1"]) / 2 <= bx_[2] and bx_[1] <= (w["top"] + w["bottom"]) / 2 <= bx_[3]]
        if len(den_) <= 15: continue
        ids_ = {id(w) for w in den_}
        fora_f_ = {_fam(w) for w in pg["ws"] if id(w) not in ids_}
        if sum(1 for w in den_ if _fam(w) not in fora_f_) < 0.8 * len(den_): continue
        # sai so o texto dos baloes (fonte propria) e cabecalho de questao escondido debaixo da imagem
        ids_ = {id(w) for w in den_ if _fam(w) not in fora_f_}
        ids_ |= {id(w) for l in pg["linhas"] if RE_CAB_Q.match(txt_puro(l)) and all(bx_[0] <= (w["x0"] + w["x1"]) / 2 <= bx_[2]
                 and bx_[1] <= (w["top"] + w["bottom"]) / 2 <= bx_[3] for w in l["ws"]) for w in l["ws"]}
        pg["ws"] = [w for w in pg["ws"] if id(w) not in ids_]
        pg["linhas"] = [l for l in pg["linhas"] if not all(id(w) in ids_ for w in l["ws"])]
        for l in pg["linhas"]:
            if any(id(w) in ids_ for w in l["ws"]):
                l["ws"] = [w for w in l["ws"] if id(w) not in ids_]
                l["x0"] = min(w["x0"] for w in l["ws"]); l["x1"] = max(w["x1"] for w in l["ws"])
    # numero de paragrafo na margem (ex.: quadradinho com "1" entre a 1a e a 2a linha do paragrafo):
    # vai para o comeco da primeira linha do paragrafo, em vez de virar uma linha solta
    tirar = []
    # numero de margem que caiu na mesma linha do texto ao lado: separa antes
    novas_ls = []
    for l in pg["linhas"]:
        ws_ = l["ws"]
        if len(ws_) >= 3 and re.fullmatch(r"\d{1,2}", ws_[0]["text"]) and ws_[1]["x0"] - ws_[0]["x1"] > 0.6 * ws_[0]["size"]:
            xs_ = sorted(o["x0"] for o in pg["linhas"] if o["col"] == l["col"] and o is not l)
            margem_ = xs_[len(xs_) // 2] if xs_ else ws_[1]["x0"]
            if os.environ.get("DEBUGN"): print("DBGM", pg["n"], txt_puro(l)[:20], round(margem_, 1), round(ws_[0]["x1"], 1), round(ws_[1]["x0"], 1))
            if ws_[0]["x1"] < margem_ - 3 and abs(ws_[1]["x0"] - margem_) < 4:
                n_ = dict(l); n_["ws"] = [ws_[0]]; n_["x0"], n_["x1"] = ws_[0]["x0"], ws_[0]["x1"]; n_["top"], n_["bottom"] = ws_[0]["top"], ws_[0]["bottom"]
                l["ws"] = ws_[1:]; l["x0"] = ws_[1]["x0"]
                base_ = [w for w in l["ws"] if not w["sup"] and not w["sub"]] or l["ws"]
                l["top"] = min(w["top"] for w in base_); l["bottom"] = max(w["bottom"] for w in l["ws"])
                novas_ls.append(n_)
    pg["linhas"] += novas_ls
    for l in pg["linhas"]:
        if os.environ.get("DEBUGN") and re.fullmatch(r"\d{1,2}", l["ws"][0]["text"]) and pg["n"] == int(os.environ["DEBUGN"]):
            print("DBGN", txt_puro(l), round(l["x0"]), round(l["top"]), l["col"], [(txt_puro(o)[:20], round(o["top"]), o["col"]) for o in pg["linhas"] if abs(o["top"] - l["top"]) < 20])
        if len(l["ws"]) != 1 or not re.fullmatch(r"\d{1,2}", l["ws"][0]["text"]): continue
        viz = [o for o in pg["linhas"] if o is not l and o["col"] == l["col"] and o["x0"] > l["x1"] + 2 and o["x0"] - l["x1"] < 3 * CORPO
               and o["bottom"] > l["top"] - 0.3 * CORPO and o["top"] < l["bottom"] + 0.3 * CORPO and len(o["ws"]) >= 3]
        if not viz: continue
        # o numero fica na altura da 1a linha do paragrafo ou entre a 1a e a 2a: a linha certa e a mais baixa
        # que comeca acima do meio do numero
        centro = (l["top"] + l["bottom"]) / 2
        cand = sorted([o for o in pg["linhas"] if o is not l and o["col"] == l["col"] and o["x0"] > l["x1"] + 2 and o["x0"] - l["x1"] < 3 * CORPO
                       and len(o["ws"]) >= 3 and centro - 1.6 * CORPO <= o["top"] <= centro + 0.6 * CORPO], key=lambda o: o["top"])
        x1max = max([o["x1"] for o in cand] or [0])
        def inicio_par(o):   # a linha de cima nao existe ou terminou o paragrafo anterior (curta e com ponto final)
            cima = [p for p in pg["linhas"] if p is not o and p["col"] == o["col"] and 0 < o["top"] - p["bottom"] < 1.2 * CORPO and p["x0"] > l["x1"]]
            return not cima or any(re.search(r"[.:!?”\"»)]$", txt_puro(p)) and p["x1"] < x1max - 15 for p in cima)
        inicios = [o for o in cand if inicio_par(o)]
        alvo = inicios[0] if inicios else min(viz, key=lambda o: o["top"])
        if os.environ.get("DEBUGN"): print("DBGA", txt_puro(l), "->", txt_puro(alvo)[:30], [txt_puro(o)[:15] for o in inicios])
        alvo["ws"] = [dict(l["ws"][0], top=alvo["top"], bottom=alvo["bottom"])] + alvo["ws"]
        tirar.append(id(l))
    pg["linhas"] = [l for l in pg["linhas"] if id(l) not in tirar]

# espaco normal entre linhas do mesmo paragrafo (mediana): paragrafo novo = espaco claramente maior que esse
_gaps = []; GAP_REG = {}
for pg in paginas:
    por_reg = collections.defaultdict(list)
    for l in pg["linhas"]:
        if abs(l["size"] - CORPO) < 0.6: por_reg[l["reg"]].append(l)
    for rk_, ls in por_reg.items():
        ls.sort(key=lambda l: l["top"])
        gr_ = []
        for a_, b_ in zip(ls, ls[1:]):
            g_ = b_["top"] - a_["bottom"]
            if 0 < g_ < CORPO: _gaps.append(g_); gr_.append(round(g_ * 2) / 2)
        # espaco mais comum desta regiao (cada prova/coluna tem o seu entrelinha)
        if len(gr_) >= 6: GAP_REG[(pg["n"], rk_)] = collections.Counter(gr_).most_common(1)[0][0]
GAP_L = sorted(_gaps)[len(_gaps) // 4] if _gaps else 0.2 * CORPO
print(f"espaco entre linhas (quartil): {GAP_L:.1f} pt")
# ------------------------------------------------------------------ figuras (deteccao pela imagem da pagina)
def render(pn, dpi, x=None, y=None, w=None, h=None, fmt="png", saida=None):
    args = ["pdftoppm", "-r", str(dpi), "-f", str(pn), "-l", str(pn), "-singlefile"]
    if x is not None: args += ["-x", str(int(x)), "-y", str(int(y)), "-W", str(int(w)), "-H", str(int(h))]
    args += ["-jpeg", "-jpegopt", "quality=80"] if fmt == "jpg" else ["-png"]
    base = saida or os.path.join(TMP, f"_tmp_{PID}_{os.getpid()}")   # nome unico: varias provas podem rodar ao mesmo tempo
    subprocess.run(args + [PDF, base], check=True, capture_output=True)
    return base + (".jpg" if fmt == "jpg" else ".png")

TEXTO_EM_FIG = {}
FIG_FORCADA = {}      # pagina -> caixas que sao desenho mesmo sendo caracteres (linhas so de simbolos, ex.: braile)
GAB_RAZAO = {}        # (pagina, top da letra) -> quanto a caixa da letra da alternativa e escura (marcada = circulo cheio)
BRANCO = {}     # recorte -> palavras de texto que encostam nele (apagadas se sairem como texto na questao)
def aplica_branco(r, extra=""):
    blob = " ".join([r.get("enunciado", r.get("texto", "")), " ".join(r.get("fontes", [])), " ".join(a["texto"] for a in r.get("alternativas", [])),
                     r.get("apos_alternativas", ""), extra])
    norm_ = lambda x: re.sub(r"\s+", "", re.sub(r"<[^>]+>|\*|\\\(|\\\)", "", x))
    blob_n = norm_(blob)
    for im in r["imagens"]:
        arq = os.path.join(OUT, im["arquivo"])
        if arq not in BRANCO: continue
        cand, (X0c, Y0c), s = BRANCO[arq]
        apagar = [bx for bxs, t in cand if len(norm_(t)) >= 3 and norm_(t) in blob_n for bx in bxs]
        if not apagar: continue
        img_ = cv2.imread(arq)
        for bx in apagar:
            X0, Y0 = int((bx[0] - 1 - X0c) * s), int((bx[1] - 1 - Y0c) * s)
            X1, Y1 = int((bx[2] + 1 - X0c) * s), int((bx[3] + 1.5 - Y0c) * s)
            img_[max(0, Y0):max(0, Y1), max(0, X0):max(0, X1)] = 255
        cv2.imwrite(arq, img_)
CORTADAS = set()
RE_FONTE_FIG = re.compile(r"(?i)(dispon[ií]vel em|disponible en|available (at|in|from)|acesso em|acceso|accessed|retrieved|consultado|adaptado|adaptad|fonte:|fuente:|source:|https?://|www\.)")
def detecta_figuras(pg):
    """Acha figuras pela imagem da pagina: apaga o texto, o que sobra de tinta e grafico.
    Linhas de texto que tem algum grafico no meio (seta, traco de fracao, raiz) viram imagem inteira."""
    page = pg["page"]; pn = pg["n"]; s = DPI_DET / 72
    img = cv2.imread(render(pn, DPI_DET), cv2.IMREAD_GRAYSCALE)
    tinta = (img < 235).astype(np.uint8)
    # alternativa marcada no caderno (letra dentro de circulo/quadrado cheio): a caixa da letra fica quase toda escura
    for l_ in pg["linhas"]:
        la_ = letra_alt(l_)
        if not la_: continue
        w0_ = l_["ws"][0]
        x0_, y0_ = int((w0_["x0"] - 1.5) * s), int((w0_["top"] - 1) * s)
        x1_, y1_ = int((w0_["x0"] + 1.1 * w0_["size"]) * s) + 1, int((w0_["bottom"] + 1) * s) + 1
        reg_ = img[max(0, y0_):y1_, max(0, x0_):x1_]
        if reg_.size: GAB_RAZAO[(pn, round(w0_["top"]))] = (reg_ < 128).mean()
    caixas_txt = np.zeros_like(tinta)
    for w in pg["ws"]:
        bx = w.get("caixa") or (w["x0"], w["top"], w["x1"], w["bottom"])
        x0, y0, x1, y1 = int(bx[0] * s) - (1 if w.get("latex") else 0), int(bx[1] * s) - (1 if w.get("latex") else 0), int(bx[2] * s) + 2, int(bx[3] * s) + 2
        tinta[max(0, y0):y1, max(0, x0):x1] = 0; caixas_txt[max(0, y0):y1, max(0, x0):x1] = 1
    Hp, Wp = tinta.shape
    tinta[: int(0.075 * Hp)] = 0; tinta[int(0.935 * Hp):] = 0       # faixa de cabecalho/rodape
    for L_ in LOGOS:       # logotipo repetido nas paginas: nao e figura (nem se junta com a figura vizinha)
        tinta[max(0, int((L_[1] - 1) * s)):int((L_[3] + 1) * s) + 1, max(0, int((L_[0] - 1) * s)):int((L_[2] + 1) * s) + 1] = 0
    # texto girado na margem, fora da area das colunas ("Baixado de www...." na vertical): marca d'agua, nao e figura
    if pg["linhas"]:
        xa_t = min(l["x0"] for l in pg["linhas"]); xb_t = max(l["x1"] for l in pg["linhas"])
        for c_ in page.chars:
            micro_ = c_.get("size", 10) < 2.5     # microtexto de seguranca (ENEM 2024): tambem nao e figura
            if not micro_ and (c_.get("upright", True) or not (c_["x0"] >= xb_t + 2 or c_["x1"] <= xa_t - 2)): continue
            tinta[max(0, int((c_["top"] - 1) * s)):int((c_["bottom"] + 1) * s) + 1, max(0, int((c_["x0"] - 1) * s)):int((c_["x1"] + 1) * s) + 1] = 0
    perto_txt = cv2.dilate(caixas_txt, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(tinta, 8)
    comps = []
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if area < 4: continue
        if area < 30 and perto_txt[y:y + h, x:x + w].any() and w < 12 and h < 12: continue   # sobra de letra
        if h <= 4 and w > 0.18 * Wp: continue          # linhas horizontais (separadores)
        # barra colorida/cinza atras do cabecalho da questao ("QUESTAO 1" sobre fundo cinza): preenchimento medido na
        # imagem original (o texto apagado deixa buracos na barra)
        if h <= max(14, 1.8 * CORPO * s) and w > 10 * h and w > 0.15 * Wp and (area > 0.8 * w * h or (img[y:y + h, x:x + w] < 235).mean() > 0.8): continue
        if w <= 4 and h > 0.25 * Hp: continue          # divisoria de colunas
        if w > 60 and h > 30:                          # moldura vazia (caixa em volta de texto)
            m = (lab[y:y + h, x:x + w] == i)
            borda = m[:4].sum() + m[-4:].sum() + m[4:-4, :4].sum() + m[4:-4, -4:].sum()
            if borda > 0.85 * area: continue
        comps.append([x / s, y / s, (x + w) / s, (y + h) / s])
    # tabelas com grade (pdfplumber) entram inteiras: as linhas horizontais da grade sao apagadas acima e a tabela
    # se partiria em pedacos
    def grade_visivel(x0_, y0_, x1_, y1_):
        """a grade tem de aparecer na pagina (tabela 'invisivel' de diagramacao nao conta): tinta na borda de cima e de baixo"""
        xa, xb = int(x0_ * s) + 2, int(x1_ * s) - 2
        if xb - xa < 10: return False
        def borda(yv):
            yy = int(yv * s)
            faixa = img[max(0, yy - 2):yy + 3, xa:xb] < 235
            return faixa.any(axis=0).mean() > 0.6
        return borda(y0_) and borda(y1_)
    # fotos embutidas no PDF entram com a caixa inteira (a parte clara da foto nao aparece como "tinta" e o recorte sairia cortado)
    for im_ in page.images:
        x0_, y0_, x1_, y1_ = max(0, im_["x0"]), max(0, im_["top"]), min(page.width, im_["x1"]), min(page.height, im_["bottom"])
        if (x1_ - x0_) < 10 or (y1_ - y0_) < 10 or (x1_ - x0_) * (y1_ - y0_) > 0.6 * page.width * page.height: continue
        if y0_ < 0.06 * page.height or y1_ > 0.95 * page.height: continue
        n_w = sum(1 for w in pg["ws"] if x0_ <= (w["x0"] + w["x1"]) / 2 <= x1_ and y0_ <= (w["top"] + w["bottom"]) / 2 <= y1_)
        if n_w > 15: continue          # imagem de fundo atras de texto
        # a caixa da foto as vezes passa por baixo da linha de texto vizinha (enunciado): apara na borda
        for _ in range(2):
            for borda_ in ("topo", "base"):
                if borda_ == "topo": faixa = [w for w in pg["ws"] if w["top"] < y0_ + 12 and w["bottom"] > y0_ and x0_ <= (w["x0"] + w["x1"]) / 2 <= x1_]
                else: faixa = [w for w in pg["ws"] if w["bottom"] > y1_ - 12 and w["top"] < y1_ and x0_ <= (w["x0"] + w["x1"]) / 2 <= x1_]
                eh_fonte_f = bool(faixa) and re.search(r"(?i)dispon[íi]vel em|acesso em|fonte:", " ".join(w["text"] for w in faixa))
                if (len(faixa) >= 5 and all(w["size"] >= 0.9 * CORPO for w in faixa)) or eh_fonte_f:
                    if borda_ == "topo": y0_ = max(w["bottom"] for w in faixa) + 1
                    else: y1_ = min(w["top"] for w in faixa) - 1
        if y1_ - y0_ < 10: continue
        # imagem que nao aparece na pagina renderizada (camada oculta) nao e figura
        reg_im = img[int(y0_ * s):int(y1_ * s) + 1, int(x0_ * s):int(x1_ * s) + 1]
        if reg_im.size == 0 or (reg_im < 235).mean() < 0.01: continue
        comps.append([x0_, y0_, x1_, y1_])
    TAB_DADOS = []     # tabelas de dados (celulas curtas): nunca sao "caixa de layout"
    try:
        for tb_ in page.find_tables():
            x0_, y0_, x1_, y1_ = tb_.bbox
            if len(tb_.rows) == 1:
                # tabela "aberta": so a faixa do cabecalho tem moldura; o corpo tem apenas o fio vertical entre as
                # colunas e o fio de baixo (ENEM 2005 "Pais X | Pais Y"). A grade e montada com esses fios.
                ab_ = tabela_aberta(page, tb_.bbox)
                if ab_:
                    x0_, y0_, x1_, y1_ = ab_
                    TAB_DADOS.append([x0_, y0_, x1_, y1_]); comps.append([x0_, y0_, x1_, y1_])
                continue
            if (x1_ - x0_) > 30 and (y1_ - y0_) > 15 and y0_ > 0.06 * page.height and y1_ < 0.95 * page.height and len(tb_.rows) >= 2:
                ext = tb_.extract() or []
                cels = [c for r in ext for c in r]
                # tabela com linha de cabecalho curta ("Pais X | Pais Y") e dados longos (listas) tambem e tabela de dados
                cab_curto_ = len(ext) >= 2 and len(ext[0]) >= 2 and all(0 < len(" ".join((c or "").split())) <= 40 for c in ext[0])
                if (cels and max(len(r) for r in ext) >= 2 and (all(len(" ".join((c or "").split())) <= 120 for c in cels) or cab_curto_)
                        and sum(1 for c in cels if (c or "").strip()) >= max(4, 0.6 * len(cels)) and not page.crop(tb_.bbox).images
                        and grade_visivel(x0_, y0_, x1_, y1_)):
                    TAB_DADOS.append([x0_, y0_, x1_, y1_]); comps.append([x0_, y0_, x1_, y1_])
    except Exception:
        pass
    comps += [list(b) for b in FIG_FORCADA.get(pn, [])]     # desenho feito de simbolos de texto (braile)
    figs = []
    for c in comps:     # junta componentes proximos (9 pt)
        figs.append(c)
    # marcadores de alternativa (bolinha "A", "a)" ...): figuras ao lado de marcadores diferentes nunca se juntam
    MARC = []
    for l_ in pg["linhas"]:
        w0 = l_["ws"][0]
        # fileira de marcadores na mesma linha ("(A)   (B)   (C)" sob uma fileira de fotos): um marcador por palavra
        soltos_ = [w for w in l_["ws"] if re.fullmatch(r"\(?[a-eA-E]\)", w["text"])]
        # (5o campo: marcador sem texto depois dele = a alternativa e a figura; "D) 7/23" tem texto e nao e rotulo de foto)
        if letra_alt(l_) and len(soltos_) < 2:
            MARC.append(((l_["top"] + l_["bottom"]) / 2, l_["x0"], l_["x1"], id(l_), len(l_["ws"]) == 1))
        if len(soltos_) >= 2:
            for w in soltos_:
                i_w = l_["ws"].index(w)
                prox_w = l_["ws"][i_w + 1] if i_w + 1 < len(l_["ws"]) else None
                MARC.append(((w["top"] + w["bottom"]) / 2, w["x0"], w["x1"], id(w), prox_w is None or prox_w in soltos_))
    def marcas_de(F):
        # marcador a esquerda da figura, na altura dela...
        ao_lado = {m[3] for m in MARC if F[1] - 2 <= m[0] <= F[3] + 2 and F[0] - 60 <= m[1] and m[2] <= F[0] + 0.3 * (F[2] - F[0]) + 5}
        # ...ou logo abaixo dela, centrado (fileira de fotos com "(A)", "(B)"... embaixo de cada uma)
        embaixo = {m[3] for m in MARC if m[4] and F[3] - 2 <= m[0] <= F[3] + 18 and F[0] - 5 <= (m[1] + m[2]) / 2 <= F[2] + 5}
        return ao_lado | embaixo
    def conflito_alt(A, B):
        ma, mb = marcas_de(A), marcas_de(B)
        return bool(ma) and bool(mb) and not (ma & mb)
    def junta(lista, tol):
        mud = True
        while mud:
            mud = False
            for a in range(len(lista)):
                for b in range(a + 1, len(lista)):
                    A, Bb = lista[a], lista[b]
                    if A[0] - tol <= Bb[2] and Bb[0] - tol <= A[2] and A[1] - tol <= Bb[3] and Bb[1] - tol <= A[3] and not conflito_alt(A, Bb):
                        lista[a] = [min(A[0], Bb[0]), min(A[1], Bb[1]), max(A[2], Bb[2]), max(A[3], Bb[3])]
                        lista.pop(b); mud = True; break
                if mud: break
        return lista
    figs = junta(figs, 9)
    linhas = pg["linhas"]
    # "caixa de layout": moldura/tabela que envolve texto corrido E uma imagem (texto de um lado, figura do outro).
    # A moldura nao e figura; dentro dela so a imagem de verdade vira figura.
    novas_f = []
    for f in figs:
        dentro_l = [l for l in linhas if f[0] <= (l["x0"] + l["x1"]) / 2 <= f[2] and f[1] <= (l["top"] + l["bottom"]) / 2 <= f[3]
                    and l["size"] >= 0.95 * CORPO and ((l["x1"] - l["x0"]) > 0.35 * (f[2] - f[0]) or RE_Q_NUM.match(txt_puro(l)) or eh_cabecalho(l) or letra_alt(l))]
        if os.environ.get("DEBUGF"): print("fig p", pn, [round(v) for v in f], "linhas dentro:", len(dentro_l), "tabela:", bool(tabela(page, f)))
        if len(dentro_l) < 3 or tabela(page, f) or any(min(f[2], t_[2]) - max(f[0], t_[0]) > 0.8 * (f[2] - f[0]) and
                                                     min(f[3], t_[3]) - max(f[1], t_[1]) > 0.8 * (f[3] - f[1]) for t_ in TAB_DADOS):
            # (a figura E a tabela de dados; moldura de pagina que CONTEM uma tabela continua sendo caixa de layout)
            novas_f.append(f); continue
        x0, y0, x1, y1 = int(f[0] * s), int(f[1] * s), int(f[2] * s) + 1, int(f[3] * s) + 1
        reg = tinta[y0:y1, x0:x1].copy()
        finos = np.zeros_like(reg); reg_seq = reg.copy()
        for kern_l, kern_g in (((1, 40), (5, 1)), ((40, 1), (1, 5))):
            lin = cv2.morphologyEx(reg_seq, cv2.MORPH_OPEN, np.ones(kern_l, np.uint8))
            grosso = cv2.morphologyEx(lin, cv2.MORPH_OPEN, np.ones(kern_g, np.uint8))
            reg_seq[(lin > 0) & (grosso == 0)] = 0      # (em sequencia, como sempre foi: o vertical ve o que sobrou)
            finos[(lin > 0) & (grosso == 0)] = 1
        # fios finos = moldura, divisoria de coluna, regua do cabecalho. Mas um desenho feito so de fios (planificacao
        # do cubo, grade) -- pequeno perto da moldura e com fios nas duas direcoes -- continua desenho
        nf_, labf_, stf_, _ = cv2.connectedComponentsWithStats(cv2.dilate(finos, np.ones((3, 3), np.uint8)), 8)
        Hr_, Wr_ = reg.shape
        manter_f = np.zeros_like(reg)
        for k in range(1, nf_):
            xk, yk, wk, hk, _a = stf_[k]
            if wk < 0.6 * Wr_ and hk < 0.6 * Hr_ and wk > 20 * s and hk > 20 * s:
                comp_ = (labf_[yk:yk + hk, xk:xk + wk] == k)
                sub_f = finos[yk:yk + hk, xk:xk + wk] & comp_
                horiz_ = cv2.morphologyEx(sub_f, cv2.MORPH_OPEN, np.ones((1, 40), np.uint8)).any()
                vert_ = cv2.morphologyEx(sub_f, cv2.MORPH_OPEN, np.ones((40, 1), np.uint8)).any()
                # moldura simples (retangulo em volta de um texto: classificado, box) nao tem fio nenhum por dentro
                miolo_f = sub_f[5:-5, 5:-5]
                # e o desenho e SO de fios (sem outra tinta dentro: quadrinho com moldura continua como antes)
                outra_ = reg[yk:yk + hk, xk:xk + wk] & (1 - finos[yk:yk + hk, xk:xk + wk])
                if horiz_ and vert_ and miolo_f.size and miolo_f.any() and outra_.mean() < 0.02:
                    manter_f[yk:yk + hk, xk:xk + wk][comp_] = 1
        reg[(finos > 0) & (manter_f == 0)] = 0
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(reg, 8)
        sub = [[(x0 + st2[k][0]) / s, (y0 + st2[k][1]) / s, (x0 + st2[k][0] + st2[k][2]) / s, (y0 + st2[k][1] + st2[k][3]) / s]
               for k in range(1, n2) if st2[k][4] >= 30]
        if os.environ.get("DEBUGF"): print("   sub:", [[round(v) for v in q] for q in junta([list(q) for q in sub], 9)], "n=", len(sub))
        novas_f += junta(sub, 9)
    figs = [f for f in novas_f if (f[2] - f[0]) > 6 and (f[3] - f[1]) > 6]
    # linha com simbolo que a fonte nao traduz ("(cid:31)" = colchete/chave grande de formula): vira imagem
    for l in linhas:
        if "(cid:" in txt_puro(l):
            # simbolo que a fonte do PDF nao traduz (parentese grande, sinal de formula): o texto fica texto e a
            # questao fica PENDENTE para transcricao lendo a imagem (nao vira foto de texto)
            l["cid"] = True
    figs = junta(figs, 2)
    # marcador pequeno com numero/letra dentro (numero de paragrafo num quadradinho etc.): nao e figura
    def eh_marcador(f):
        if not ((f[2] - f[0]) < 2.5 * CORPO and (f[3] - f[1]) < 2.5 * CORPO): return False
        dentro_w = [w for w in pg["ws"] if f[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= f[2] + 1 and f[1] - 1 <= (w["top"] + w["bottom"]) / 2 <= f[3] + 1]
        ok_ = bool(dentro_w) and all(re.fullmatch(r"\(?[0-9A-Za-z]{1,3}[.)]?", w["text"]) for w in dentro_w)
        if ok_ and len(dentro_w) == 1 and re.fullmatch(r"\(?[A-Ea-e][.)]?", dentro_w[0]["text"]):
            # letra de alternativa dentro de circulo/quadrado cheio = alternativa marcada no caderno (gabarito embutido)
            x0_, y0_, x1_, y1_ = int(f[0] * s), int(f[1] * s), int(f[2] * s) + 1, int(f[3] * s) + 1
            if (img[y0_:y1_, x0_:x1_] < 128).mean() > 0.4:
                pass
        return ok_
    figs = [f for f in figs if not eh_marcador(f)]
    # decoracao do cabecalho da questao (caixa preta com o numero, faixa/linha ao lado de "QUESTAO 12"): nao e figura
    def enfeite_cab(f):
        if (f[3] - f[1]) > 2.6 * CORPO: return False
        return any((eh_cabecalho(l) is not None or (linha_estrutural(l) and not letra_alt(l))) and l["top"] >= f[1] - 3 and l["bottom"] <= f[3] + 3
                   and min(l["x1"], f[2]) - max(l["x0"], f[0]) > -15 for l in linhas)
    figs = [f for f in figs if not enfeite_cab(f)]
    def larg_col(l): return l["col"][1] - l["col"][0]
    esq_col = {}
    for c in {l["col"] for l in linhas}:
        xs = sorted(l["x0"] for l in linhas if l["col"] == c and abs(l["size"] - CORPO) < 0.6)
        esq_col[c] = xs[len(xs) // 10] if xs else c[0]
    for l in linhas:   # linha de rotulos (numeros de eixo, palavras soltas bem espacadas)
        toks = [w["text"] for w in l["ws"]]
        numeros = sum(1 for t in toks if re.fullmatch(r"[\d.,:%()\-–+×x/°]+", t))
        gaps = [b["x0"] - a["x1"] for a, b in zip(l["ws"], l["ws"][1:])]
        l["rotulo"] = len(toks) >= 2 and (numeros >= 0.5 * len(toks) or (gaps and max(gaps) > 3 * l["size"]))
    # linha de rotulos muito espacados (ex.: "F" de uma figura ... "F" da figura ao lado) vira um pedaco por rotulo,
    # para cada rotulo poder ir com a sua figura
    novas_l = []
    for l in linhas:
        ws_l = sorted(l["ws"], key=lambda w: w["x0"])
        cortes = [k for k in range(1, len(ws_l)) if ws_l[k]["x0"] - ws_l[k - 1]["x1"] > 3 * l["size"]]
        if l["rotulo"] and cortes and len(ws_l) <= 8:
            ini = 0
            for k in cortes + [len(ws_l)]:
                parte = ws_l[ini:k]; ini = k
                nl = dict(l); nl["ws"] = parte
                nl["x0"] = min(w["x0"] for w in parte); nl["x1"] = max(w["x1"] for w in parte)
                nl["rotulo"] = True
                novas_l.append(nl)
        else:
            novas_l.append(l)
    # quadro de legenda do grafico ("Com poluentes domesticos  - . - . -" / "Com poluentes industriais ......"): moldura
    # pequena, com poucas linhas curtas, colada na figura -> faz parte da figura (a legenda explica o desenho)
    for r_ in page.rects:
        rx0, ry0, rx1, ry1 = r_["x0"], r_["top"], r_["x1"], r_["bottom"]
        if not (15 < rx1 - rx0 < 0.6 * page.width and 6 < ry1 - ry0 < 6 * CORPO): continue
        # a moldura tem de aparecer (retangulo branco de fundo de linha nao e quadro de legenda)
        bx_ = img[max(0, int(ry0 * s) - 1):int(ry0 * s) + 2, int(rx0 * s):int(rx1 * s)]
        by_ = img[int(ry0 * s):int(ry1 * s), max(0, int(rx0 * s) - 1):int(rx0 * s) + 2]
        if not (bx_.size and by_.size and (bx_ < 200).any(axis=0).mean() > 0.7 and (by_ < 200).any(axis=1).mean() > 0.7): continue
        dentro_r = [l for l in novas_l if rx0 - 1 <= l["x0"] and l["x1"] <= rx1 + 1 and ry0 - 1 <= l["top"] and l["bottom"] <= ry1 + 1]
        if not dentro_r or len(dentro_r) > 5 or any(len(l["ws"]) > 6 or linha_estrutural(l) for l in dentro_r): continue
        for f in figs:
            perto_ = (0 <= ry0 - f[3] <= 25 or 0 <= f[1] - ry1 <= 25) and min(rx1, f[2]) - max(rx0, f[0]) > 0
            if perto_:
                f[0], f[1], f[2], f[3] = min(f[0], rx0), min(f[1], ry0), max(f[2], rx1), max(f[3], ry1)
                break
    # linha que atravessa a borda de uma figura/tabela (celula da tabela + texto ao lado na mesma altura, ex.: "Tempo de
    # uso   Supondo que o mes..."): vira duas linhas, a de dentro e a de fora, para o texto de fora nao entrar na figura
    partidas = []
    for l in novas_l:
        feito = False
        for f in figs:
            if min(l["bottom"], f[3]) - max(l["top"], f[1]) <= 0.3 * (l["bottom"] - l["top"]): continue
            dentro_ = [w for w in l["ws"] if f[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= f[2] + 1]
            fora_ = [w for w in l["ws"] if w not in dentro_]
            if not dentro_ or not fora_: continue
            xd1, xf0 = max(w["x1"] for w in dentro_), min(w["x0"] for w in fora_)
            xd0, xf1 = min(w["x0"] for w in dentro_), max(w["x1"] for w in fora_)
            if not (xf0 - xd1 > 0.5 * l["size"] or xd0 - xf1 > 0.5 * l["size"]): continue
            for parte in (dentro_, fora_):
                nl = dict(l); nl["ws"] = sorted(parte, key=lambda w: w["x0"])
                nl["x0"] = min(w["x0"] for w in parte); nl["x1"] = max(w["x1"] for w in parte)
                nl["size"] = collections.Counter(round(w["size"], 1) for w in parte if not w["sup"] and not w["sub"]).most_common(1)[0][0] \
                    if any(not w["sup"] and not w["sub"] for w in parte) else l["size"]
                nl["top"] = min(w["top"] for w in parte); nl["bottom"] = max(w["bottom"] for w in parte)
                partidas.append(nl)
            feito = True; break
        if not feito: partidas.append(l)
    novas_l = partidas
    linhas[:] = novas_l
    for l in linhas:   # linha que faz parte de um paragrafo (tem vizinha longa colada) nao e rotulo de figura
        # rotulo curto e fora da margem (ex.: "Tempo (min)" centralizado sob o grafico) nao e linha de paragrafo,
        # mesmo que o paragrafo seguinte comece logo abaixo
        # ...a nao ser que seja a ultima linha de um paragrafo: a linha de cima, colada, comeca no mesmo x e e mais longa
        # (texto ao lado de uma tabela: "de R$ 0,40, o consumo..." / "e de aproximadamente")
        fim_de_par = any(o is not l and o["col"] == l["col"] and abs(o["size"] - l["size"]) < 1 and abs(o["x0"] - l["x0"]) < 2.5
                         and (o["x1"] - o["x0"]) > (l["x1"] - l["x0"]) and 0 <= l["top"] - o["bottom"] < 0.6 * CORPO and len(o["ws"]) >= 4
                         for o in linhas)
        if (l["x1"] - l["x0"]) < 0.5 * larg_col(l) and abs(l["x0"] - esq_col[l["col"]]) > 8 and len(l["ws"]) <= 4 and not fim_de_par:
            l["em_par"] = False; continue
        if fim_de_par: l["em_par"] = True; continue
        l["em_par"] = any(o is not l and o["col"] == l["col"] and abs(o["size"] - l["size"]) < 1 and not o["rotulo"] and
                          (o["x1"] - o["x0"]) > 0.6 * larg_col(o) and
                          (0 <= l["top"] - o["bottom"] < 0.6 * CORPO or 0 <= o["top"] - l["bottom"] < 0.6 * CORPO)
                          for o in linhas)
    # absorve texto: linhas dentro da figura, rotulos em volta (linhas curtas a ate 8 pt), e linhas cortadas por grafico
    def eh_fonte_l(l):
        """linha de fonte/credito ("Disponivel em...", "Acesso em...") ou continuacao colada a uma delas: fica texto"""
        if RE_FONTE_FIG.search(txt_puro(l)) or re.match(r"(?i)^(foto|imagem|ilustra[çc][ãa]o|fonte)\s*:", txt_puro(l)): return True
        return any(o is not l and abs(o["size"] - l["size"]) < 0.5 and RE_FONTE_FIG.search(txt_puro(o))
                   and (0 <= l["top"] - o["bottom"] < 0.8 * CORPO or 0 <= o["top"] - l["bottom"] < 0.8 * CORPO)
                   and min(o["x1"], l["x1"]) - max(o["x0"], l["x0"]) > -5 for o in linhas)
    mud = True
    while mud:
        mud = False
        # linha de rotulos que atravessa varias figuras (ex.: "Transportador ... Transportador ... Citocromo c" dentro de um
        # esquema grande): as figuras e a linha sao uma ilustracao so -> junta tudo
        for l in linhas:
            if l.get("fig") is not None: continue
            hl = l["bottom"] - l["top"]
            toc = [f for f in figs if min(l["bottom"], f[3]) - max(l["top"], f[1]) > 0.3 * hl and min(l["x1"], f[2]) - max(l["x0"], f[0]) > 0]
            if len(toc) < 2 or any(conflito_alt(a_, b_) for a_ in toc for b_ in toc if a_ is not b_): continue
            if linha_estrutural(l): continue     # cabecalho de questao/alternativa/titulo nunca e rotulo
            cob = sum(min(l["x1"], f[2]) - max(l["x0"], f[0]) for f in toc)
            if cob < 0.5 * (l["x1"] - l["x0"]) or l["em_par"]: continue
            g = toc[0]
            for f in toc[1:]:
                g[0], g[1], g[2], g[3] = min(g[0], f[0]), min(g[1], f[1]), max(g[2], f[2]), max(g[3], f[3]); f[0] = f[2] = -999
            g[0] = min(g[0], l["x0"]); g[2] = max(g[2], l["x1"]); l["fig"] = 1; mud = True
            figs = [f for f in figs if f[0] != -999]
        for f in figs:
            for l in linhas:
                if l.get("fig") is not None: continue
                ov_x = min(l["x1"], f[2]) - max(l["x0"], f[0]); ov_y = min(l["bottom"], f[3]) - max(l["top"], f[1])
                dentro = ov_x > 0.5 * (l["x1"] - l["x0"]) and ov_y > 0.3 * (l["bottom"] - l["top"])
                curta = (l["x1"] - l["x0"]) < 0.6 * larg_col(l)
                perto = (ov_x > 0.3 * (l["x1"] - l["x0"]) and (-8 < f[1] - l["bottom"] <= 8 or -8 < l["top"] - f[3] <= 8)) or \
                        (ov_y > 0 and (sum(1 for w in l["ws"] if not w["sup"] and not w["sub"]) <= 3 or l["rotulo"]) and (-3 <= f[0] - l["x1"] <= 15 or -3 <= l["x0"] - f[2] <= 15)
                         and not l.get("em_par")) or \
                        (re.fullmatch(r"\d{1,2}|[A-Za-z]", txt_puro(l).strip()) is not None and ov_x > 0 and -2 < l["top"] - f[3] <= 14)
                # (fim de paragrafo ao lado da figura nao e rotulo; numero/letra logo embaixo da foto -- "1", "2", "3" -- e da foto)
                # grafico pequeno no meio de uma linha (seta de equacao): o que esta na mesma altura, colado, vai junto
                cy = (l["top"] + l["bottom"]) / 2
                negr = all(w["bold"] for w in l["ws"])
                legenda = negr and curta and ov_x > 0.8 * (l["x1"] - l["x0"]) and 0 <= l["top"] - f[3] <= 14
                eq = (f[3] - f[1]) < 2.2 * CORPO and f[1] - 2 <= cy <= f[3] + 2 and (0 <= f[0] - l["x1"] <= 25 or 0 <= l["x0"] - f[2] <= 25) \
                     and (l["x1"] - l["x0"]) < 0.5 * larg_col(l) and not l["em_par"]
                # linha inteira dentro de uma tabela de dados: e celula da tabela (a tabela sai inteira, nunca pela metade)
                if dentro and any(t_[0] - 2 <= l["x0"] and l["x1"] <= t_[2] + 2 and t_[1] - 2 <= l["top"] and l["bottom"] <= t_[3] + 2
                                  and f[0] - 2 <= t_[0] and t_[2] <= f[2] + 2 and f[1] - 2 <= t_[1] and t_[3] <= f[3] + 2 for t_ in TAB_DADOS):
                    l["fig"] = 1; mud = True; continue
                protegida = linha_estrutural(l) or re.match(r"^((?i:quest[ãa]o)\s+\d|\(?[a-eA-E]\)\s|\d{1,3}\s*[.)]\s)", txt_puro(l))
                if protegida: continue
                alinhada_texto = abs(l["x0"] - esq_col[l["col"]]) < 4 and l["size"] >= 0.95 * CORPO and not l["rotulo"]
                if RE_FONTE_FIG.search(txt_puro(l)): continue   # "Disponivel em..." fica como fonte (texto)
                if any(o is not l and o.get("fig") is None and abs(o["size"] - l["size"]) < 0.5 and RE_FONTE_FIG.search(txt_puro(o))
                                      and (0 <= l["top"] - o["bottom"] < 0.8 * CORPO or 0 <= o["top"] - l["bottom"] < 0.8 * CORPO)
                                      and min(o["x1"], l["x1"]) - max(o["x0"], l["x0"]) > -5 for o in linhas): continue   # continuacao da fonte
                # paragrafo do texto (alinhado na margem, com vizinhas) sem nenhum grafico por perto nao e parte da figura,
                # mesmo que a figura tenha crescido ate ele (evita a figura "engolir" o enunciado em cascata)
                if sum(1 for w in l["ws"] if not w["sup"] and not w["sub"] and len(w["text"]) > 1) >= 4 and (l["x1"] - l["x0"]) > 0.45 * larg_col(l) and not tinta[max(0, int((l["top"] - 2) * s)):int((l["bottom"] + 2) * s), int(l["x0"] * s):int(l["x1"] * s)].any(): continue
                if l["em_par"] and not tinta[max(0, int((l["top"] - 6) * s)):int((l["bottom"] + 6) * s), int(l["x0"] * s):int(l["x1"] * s)].any(): continue
                # rotulo curto que encosta/entra na borda da figura (ex.: "Calcada" com a seta apontando para dentro)
                encosta = ov_x > 0 and ov_y > -2 and len(l["ws"]) <= 3 and curta and not l["em_par"] and not alinhada_texto
                # titulo da figura: negrito, curto, centralizado sobre a figura, logo acima dela (ate 12 pt)
                cx_l = (l["x0"] + l["x1"]) / 2; cx_f = (f[0] + f[2]) / 2
                titulo = (negr and len(l["ws"]) <= 14 and (l["x1"] - l["x0"]) <= 1.1 * (f[2] - f[0]) and abs(cx_l - cx_f) < 0.15 * (f[2] - f[0])
                          and 0 <= f[1] - l["bottom"] <= 12 and not re.match(r"(?i)^\W*text(o|s)?\s*\d", txt_puro(l)) and not RE_Q_NUM.match(txt_puro(l)) and eh_cabecalho(l) is None)
                if dentro or eq or legenda or encosta or titulo or (perto and (curta or l["rotulo"]) and not l["em_par"] and not alinhada_texto):
                    if os.environ.get("DEBUGF"): print("  absorve p", pn, [round(v) for v in f], txt_puro(l)[:40], "dentro" if dentro else "eq" if eq else "legenda" if legenda else "perto")
                    l["fig"] = 1; f[0] = min(f[0], l["x0"]); f[1] = min(f[1], l["top"]); f[2] = max(f[2], l["x1"]); f[3] = max(f[3], l["bottom"]); mud = True
        if mud: figs = junta(figs, 2)
        if not mud:
            # legendas entre duas partes da mesma ilustracao (ex.: nomes das moleculas entre as linhas de estruturas)
            for A in figs:
                for Bf in figs:
                    if A is Bf or Bf[1] < A[3] or Bf[1] - A[3] > 4 * CORPO: continue
                    if min(A[2], Bf[2]) - max(A[0], Bf[0]) < 0.5 * min(A[2] - A[0], Bf[2] - Bf[0]): continue
                    meio_pag = page.width / 2
                    lado = lambda F: 0 if F[2] <= meio_pag + 5 else (1 if F[0] >= meio_pag - 5 else 2)
                    if lado(A) != lado(Bf): continue
                    if tabela(page, A) or tabela(page, Bf) or conflito_alt(A, Bf): continue     # tabela transcrevivel fica separada da foto
                    meio = [l for l in linhas if l.get("fig") is None and l["top"] >= A[3] - 2 and l["bottom"] <= Bf[1] + 2
                            and min(l["x1"], max(A[2], Bf[2]) + 2 * CORPO) - max(l["x0"], min(A[0], Bf[0]) - 2 * CORPO) > 0]
                    if any(not l["rotulo"] and l["size"] >= 0.95 * CORPO and (l["x1"] - l["x0"]) > 0.6 * larg_col(l) for l in meio): continue
                    if any(letra_alt(l) or eh_cabecalho(l) is not None or re.match(r"^((?i:quest[ãa]o)\s+\d|\(?[a-eA-E]\)\s|\d{1,3}\s*[.)]\s)", txt_puro(l)) for l in meio): continue
                    # marcador de alternativa na mesma coluna, entre as duas figuras: cada figura e de uma alternativa
                    if any((letra_alt(l) and (eh_bolinha(l["ws"][0]["fontname"]) or abs(l["x0"] - esq_col[l["col"]]) < 6))
                           and A[3] - 2 <= (l["top"] + l["bottom"]) / 2 <= Bf[1] + 2 + (Bf[3] - Bf[1])
                           and min(A[0], Bf[0]) - 40 <= l["x0"] <= max(A[2], Bf[2]) for l in linhas): continue
                    for l in meio:
                        l["fig"] = 1; A[0] = min(A[0], l["x0"]); A[2] = max(A[2], l["x1"]); A[3] = max(A[3], l["bottom"])
                    A[0] = min(A[0], Bf[0]); A[1] = min(A[1], Bf[1]); A[2] = max(A[2], Bf[2]); A[3] = max(A[3], Bf[3])
                    Bf[0] = Bf[2] = -999; mud = True
                    break
                if mud: break
            figs = [f for f in figs if f[0] != -999]
            if mud: figs = junta(figs, 2)
        if not mud:
            # partes da mesma ilustracao lado a lado (ex.: esquema | seta | esquema): mesma faixa de altura,
            # mesma regiao da pagina e nenhum texto entre elas -> um recorte so
            def reg_de(F):
                cx, cy = (F[0] + F[2]) / 2, (F[1] + F[3]) / 2
                for k, r in enumerate(pg["regs"]):
                    if r[0] <= cx < r[1] and r[2] <= cy < r[3]: return k
                return None
            for A in figs:
                for Bf in figs:
                    if A is Bf or Bf[0] < A[2]: continue
                    ov = min(A[3], Bf[3]) - max(A[1], Bf[1])
                    if ov < 0.5 * min(A[3] - A[1], Bf[3] - Bf[1]): continue
                    if Bf[0] - A[2] > 0.25 * page.width or reg_de(A) != reg_de(Bf): continue
                    if tabela(page, A) or tabela(page, Bf) or conflito_alt(A, Bf): continue
                    y0_, y1_ = max(A[1], Bf[1]), min(A[3], Bf[3])
                    entre = [l for l in linhas if l.get("fig") is None and l["x1"] > A[2] - 1 and l["x0"] < Bf[0] + 1
                             and l["bottom"] > y0_ and l["top"] < y1_]
                    if entre: continue
                    # o recorte unido nao pode engolir texto que nao e de nenhuma das duas (ex.: tirinha alta a esquerda e
                    # tirinha baixa a direita com o enunciado embaixo dela: sao duas figuras)
                    U_ = [min(A[0], Bf[0]), min(A[1], Bf[1]), max(A[2], Bf[2]), max(A[3], Bf[3])]
                    dentro_de = lambda l, F: F[0] - 2 <= (l["x0"] + l["x1"]) / 2 <= F[2] + 2 and F[1] - 2 <= (l["top"] + l["bottom"]) / 2 <= F[3] + 2
                    if any(l.get("fig") is None and len(l["ws"]) >= 3 and dentro_de(l, U_) and not dentro_de(l, A) and not dentro_de(l, Bf)
                           for l in linhas): continue
                    A[0] = min(A[0], Bf[0]); A[1] = min(A[1], Bf[1]); A[2] = max(A[2], Bf[2]); A[3] = max(A[3], Bf[3])
                    Bf[0] = Bf[2] = -999; mud = True
                    break
                if mud: break
            figs = [f for f in figs if f[0] != -999]
            if mud: figs = junta(figs, 2)
    figs = [f for f in figs if (f[2] - f[0]) > 2 and (f[3] - f[1]) > 2]
    # marcador pequeno com numero/letra dentro (ex.: numero de paragrafo num quadradinho): nao e figura, o numero fica texto
    sem_marc = []
    for f in figs:
        if (f[2] - f[0]) < 2.5 * CORPO and (f[3] - f[1]) < 2.5 * CORPO:
            dentro_m = [l for l in linhas if l.get("fig") is not None and f[0] - 1 <= (l["x0"] + l["x1"]) / 2 <= f[2] + 1 and f[1] - 1 <= (l["top"] + l["bottom"]) / 2 <= f[3] + 1]
            if dentro_m and all(re.fullmatch(r"[0-9A-Za-z]{1,3}", txt_puro(l).strip()) for l in dentro_m):
                for l in dentro_m: l["fig"] = None
                continue
        sem_marc.append(f)
    figs = sem_marc
    # moldura (inclusive tracejada) em volta de texto: nao e figura; o texto volta a ser texto
    reais = []
    for f in figs:
        x0, y0, x1, y1 = int(f[0] * s), int(f[1] * s), int(f[2] * s), int(f[3] * s)
        if x1 - x0 > 30 and y1 - y0 > 20:
            miolo = tinta[y0 + 6:y1 - 6, x0 + 6:x1 - 6]; total = tinta[y0:y1, x0:x1]
            if total.sum() > 0 and miolo.sum() < 0.03 * total.sum():
                for l in linhas:
                    cx, cy = (l["x0"] + l["x1"]) / 2, (l["top"] + l["bottom"]) / 2
                    if f[0] <= cx <= f[2] and f[1] <= cy <= f[3]: l["fig"] = None
                continue
        reais.append(f)
    figs = reais
    # a figura cobre a caixa inteira do que foi absorvido (fracao/raiz tem numerador e denominador fora da "linha")
    for f in figs:
        for l in linhas:
            if l.get("fig") is None or not (f[0] - 1 <= (l["x0"] + l["x1"]) / 2 <= f[2] + 1 and f[1] - 1 <= (l["top"] + l["bottom"]) / 2 <= f[3] + 1): continue
            for w in l["ws"]:
                bx = w.get("caixa") or (w["x0"], w["top"], w["x1"], w["bottom"])
                f[0] = min(f[0], bx[0]); f[1] = min(f[1], bx[1]); f[2] = max(f[2], bx[2]); f[3] = max(f[3], bx[3])
    if os.environ.get("DEBUGF"): print("  antes-cresce p", pn, [[round(v) for v in f] for f in figs])
    # protecao: desenho que continua para fora do recorte (titulo do grafico, moldura, ultima linha da tabela):
    # o recorte cresce ate pegar o desenho inteiro, desde que nao engula paragrafo de texto
    for _ in range(3):
        cresceu = False
        for k_, f in enumerate(figs):
            for i in range(1, n):
                x, y, w, h, area = st[i]
                if area < 40 or (h <= 4 and w > 0.18 * Wp) or (w <= 4 and h > 0.25 * Hp): continue
                if w / s < 2.5 * CORPO and h / s < 2.5 * CORPO: continue      # pedaco pequeno (letra desenhada) nao puxa o recorte
                c = [x / s, y / s, (x + w) / s, (y + h) / s]
                if c[2] < f[0] or c[0] > f[2] or c[3] < f[1] or c[1] > f[3]: continue
                if max(f[0] - c[0], c[2] - f[2], f[1] - c[1], c[3] - f[3]) <= 3: continue
                if any(j != k_ and G[0] - 2 <= c[0] and c[2] <= G[2] + 2 and G[1] - 2 <= c[1] and c[3] <= G[3] + 2 for j, G in enumerate(figs)): continue
                if conflito_alt(f, c): continue
                nb = [min(f[0], c[0]), min(f[1], c[1]), max(f[2], c[2]), max(f[3], c[3])]
                novas_l = [l for l in linhas if l.get("fig") is None and nb[0] - 1 <= (l["x0"] + l["x1"]) / 2 <= nb[2] + 1 and nb[1] - 1 <= (l["top"] + l["bottom"]) / 2 <= nb[3] + 1]
                if any(l["em_par"] or eh_fonte_l(l) or RE_Q_NUM.match(txt_puro(l)) or linha_estrutural(l) for l in novas_l): continue
                if (nb[2] - nb[0]) * (nb[3] - nb[1]) > 2 * (f[2] - f[0]) * (f[3] - f[1]): continue
                if len(novas_l) > 3: continue
                for l in novas_l: l["fig"] = 1
                f[:] = nb; cresceu = True
        if not cresceu: break
    # palavras soltas dentro de figura (ex.: numero de eixo na mesma altura da bolinha) vao para a figura
    for l in linhas:
        if l.get("fig") is not None or eh_fonte_l(l) or (linha_estrutural(l) and not letra_alt(l)): continue
        manter = [w for w in l["ws"] if (w is l["ws"][0] and eh_bolinha(w["fontname"])) or not any(f[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= f[2] + 1 and f[1] - 1 <= (w["top"] + w["bottom"]) / 2 <= f[3] + 1 for f in figs)]
        if len(manter) < len(l["ws"]):
            if eh_bolinha(l["ws"][0]["fontname"]):
                l["ws"] = manter or l["ws"]
                if not manter: l["fig"] = 1
                else: l["x0"] = min(w["x0"] for w in manter); l["x1"] = max(w["x1"] for w in manter)
            elif l.get("rotulo") or (l["x1"] - l["x0"]) < 0.4 * larg_col(l):
                # rotulo curto com parte dentro da figura (ex.: "450 m" com o "m" passando da borda): vai inteiro
                # para a figura, e a figura cresce para pegar o rotulo todo (unidade nao vira texto solto)
                f_ = next(f for f in figs if any(f[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= f[2] + 1 and f[1] - 1 <= (w["top"] + w["bottom"]) / 2 <= f[3] + 1 for w in l["ws"]))
                if (l["x1"] - l["x0"]) < 0.4 * larg_col(l):
                    l["fig"] = 1
                    f_[0] = min(f_[0], l["x0"]); f_[1] = min(f_[1], l["top"]); f_[2] = max(f_[2], l["x1"]); f_[3] = max(f_[3], l["bottom"])
                elif manter:
                    l["ws"] = manter; l["x0"] = min(w["x0"] for w in manter); l["x1"] = max(w["x1"] for w in manter)
                else:
                    l["fig"] = 1
    # pedaco estreito colado ao lado de uma figura e dentro da altura dela (ex.: titulo de eixo escrito na vertical)
    # e parte dessa figura
    mud_l = True
    while mud_l:
        mud_l = False
        for S in figs:
            if min(S[2] - S[0], S[3] - S[1]) > 2 * CORPO: continue
            for G in figs:
                if G is S or (G[2] - G[0]) * (G[3] - G[1]) <= (S[2] - S[0]) * (S[3] - S[1]): continue
                if S[1] >= G[1] - 5 and S[3] <= G[3] + 5 and (0 <= G[0] - S[2] <= 15 or 0 <= S[0] - G[2] <= 15) and not conflito_alt(G, S):
                    G[0], G[1], G[2], G[3] = min(G[0], S[0]), min(G[1], S[1]), max(G[2], S[2]), max(G[3], S[3])
                    figs.remove(S); mud_l = True; break
            if mud_l: break
    if os.environ.get("DEBUGF"): print("  antes-split p", pn, [[round(v) for v in f] for f in figs])
    # uma figura (foto unica no PDF, ou fotos coladas) com DUAS OU MAIS letras de alternativa embaixo ("(B)  (C)  (D)"):
    # uma imagem por alternativa, cortando no meio entre as letras e aparando o branco
    divididas = []
    for f in figs:
        mb_ = sorted([m for m in MARC if m[4] and f[3] - 2 <= m[0] <= f[3] + 18 and f[0] - 5 <= (m[1] + m[2]) / 2 <= f[2] + 5], key=lambda m: m[1])
        if len(mb_) < 2 or (mb_[-1][2] - mb_[0][1]) < 0.4 * (f[2] - f[0]):
            divididas.append(f); continue
        cx_ = [(m[1] + m[2]) / 2 for m in mb_]
        cortes_ = [f[0]] + [(a + b) / 2 for a, b in zip(cx_, cx_[1:])] + [f[2]]
        for a, b in zip(cortes_, cortes_[1:]):
            x0p, x1p = int(a * s), int(b * s) + 1
            reg_p = tinta[int(f[1] * s):int(f[3] * s) + 1, x0p:x1p]
            cols_ = np.nonzero(reg_p.any(axis=0))[0]
            if len(cols_) == 0: continue
            divididas.append([(x0p + cols_[0]) / s, f[1], (x0p + cols_[-1] + 1) / s, f[3]])
    figs = divididas
    # alternativas em imagem: varias "bolinhas" (A, B, C...) ao lado da mesma figura -> corta uma imagem por alternativa
    bol = [l for l in linhas if (eh_bolinha(l["ws"][0]["fontname"]) and re.fullmatch(r"([A-Ea-e])\1?", l["ws"][0]["text"]))
           or re.fullmatch(r"\(?[a-eA-E]\)", txt_puro(l).strip()) or (ALT_PONTO and re.fullmatch(r"[A-E]\.", txt_puro(l).strip()))]
    novas = []
    for f in figs:
        bs = [l for l in bol if l["top"] < f[3] and l["bottom"] > f[1] - 12 and f[0] - 30 <= l["x0"] <= f[2]]
        if len(bs) == 0: novas.append(f); continue
        if len(bs) == 1: novas.append({"bbox": f, "alt": bs[0]}); continue
        tinta_full = (img < 200)
        linhas_b = []
        for b in sorted(bs, key=lambda l: (l["top"], l["x0"])):
            if linhas_b and abs(linhas_b[-1][0]["top"] - b["top"]) < 4: linhas_b[-1].append(b)
            else: linhas_b.append([b])
        def corte(v0, v1, eixo, lim0, lim1):
            """procura, entre v0 e v1 (pt), a faixa com menos tinta (eixo 0 = linhas horizontais)"""
            a0, a1 = int(v0 * s), int(v1 * s)
            if a1 <= a0: return (v0 + v1) / 2
            if eixo == 0: perfil = tinta_full[a0:a1, int(lim0 * s):int(lim1 * s)].sum(axis=1)
            else: perfil = tinta_full[int(lim0 * s):int(lim1 * s), a0:a1].sum(axis=0)
            mn = perfil.min(); idx = [k for k, v in enumerate(perfil) if v == mn]
            # maior sequencia de minimos
            best = (0, idx[0], idx[0]); ini = idx[0]; prev = idx[0]
            for k in idx[1:] + [None]:
                if k is not None and k == prev + 1: prev = k; continue
                if prev - ini > best[0]: best = (prev - ini, ini, prev)
                if k is not None: ini = prev = k
            return (a0 + (best[1] + best[2]) / 2) / s
        ys = [f[1] - 2]
        for i in range(1, len(linhas_b)):
            ys.append(corte(max(x["bottom"] for x in linhas_b[i - 1]), min(x["top"] for x in linhas_b[i]), 0, f[0], f[2]))
        ys.append(f[3] + 2)
        for i, row in enumerate(linhas_b):
            row = sorted(row, key=lambda l: l["x0"])
            for j, b in enumerate(row):
                x0 = b["ws"][0]["x1"] + 1
                x1 = corte(b["ws"][0]["x1"] + 5, row[j + 1]["x0"], 1, ys[i], ys[i + 1]) if j + 1 < len(row) else f[2]
                sub = [x0, ys[i], x1, ys[i + 1]]
                sub_f = sub; sub_f.append(None)
                novas.append({"bbox": sub[:4], "alt": b})
    figs = [x if isinstance(x, dict) else {"bbox": x, "alt": None} for x in novas]
    for F in figs:
        f = F["bbox"]
        n_txt = sum(1 for w in pg["ws"] if w["size"] >= 0.95 * CORPO and f[0] <= (w["x0"] + w["x1"]) / 2 <= f[2] and f[1] <= (w["top"] + w["bottom"]) / 2 <= f[3])
        if n_txt >= 30: TEXTO_EM_FIG[(pn, tuple(round(v, 1) for v in f))] = n_txt
    if os.environ.get("DEBUG") and pn in [int(x) for x in os.environ["DEBUG"].split(",")]:
        dbg = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        for c in comps: cv2.rectangle(dbg, (int(c[0]*s), int(c[1]*s)), (int(c[2]*s), int(c[3]*s)), (0, 200, 0), 1)
        for F in figs:
            f = F["bbox"]; cv2.rectangle(dbg, (int(f[0]*s), int(f[1]*s)), (int(f[2]*s), int(f[3]*s)), (0, 0, 255), 2)
        cv2.imwrite(os.path.join(B, "piloto", "tmp", f"dbg_{PID}_p{pn}.png"), dbg)
    # protecao: desenho que comeca dentro de uma figura e continua para fora dela = recorte cortado
    for F in figs:
        f = F["bbox"]
        if F.get("alt") is not None: continue
        for i in range(1, n):
            x, y, w, h, area = st[i]
            if area < 40 or (h <= 4 and w > 0.18 * Wp) or (w <= 4 and h > 0.25 * Hp): continue
            if w / s < 2.5 * CORPO and h / s < 2.5 * CORPO: continue
            c = [x / s, y / s, (x + w) / s, (y + h) / s]
            if c[2] < f[0] or c[0] > f[2] or c[3] < f[1] or c[1] > f[3]: continue
            sai = max(f[0] - c[0], c[2] - f[2], f[1] - c[1], c[3] - f[3])
            dentro_txt = [l for l in linhas if l.get("fig") is None and len(l["ws"]) >= 4 and c[0] <= (l["x0"] + l["x1"]) / 2 <= c[2] and c[1] <= (l["top"] + l["bottom"]) / 2 <= c[3]]
            if dentro_txt: continue          # moldura de diagramacao em volta de texto + figura: nao e corte
            if sai > 4 and not any(G is not F and G["bbox"][0] - 2 <= c[0] and c[2] <= G["bbox"][2] + 2 and G["bbox"][1] - 2 <= c[1] and c[3] <= G["bbox"][3] + 2 for G in figs):
                CORTADAS.add((pn, tuple(round(v, 1) for v in f)))
                if os.environ.get("DEBUGF"): print("  cortada? p", pn, [round(v) for v in f], "comp", [round(v) for v in c])
                break
    # protecao: tinta (desenho) entre as palavras de uma linha de texto que nao virou figura = trecho desenhado
    # sem texto (ex.: "α =" feito com curvas). O texto sairia faltando um pedaco sem aviso -> marca a linha.
    resto = tinta.copy()
    for F in figs:
        f = F["bbox"]; resto[max(0, int(f[1] * s) - 2):int(f[3] * s) + 3, max(0, int(f[0] * s) - 2):int(f[2] * s) + 3] = 0
    for l in linhas:
        if l.get("fig") is not None: continue
        ws_l = sorted([w for w in l["ws"] if not w["sup"] and not w["sub"]], key=lambda w: w["x0"])
        for a_, b_ in zip(ws_l, ws_l[1:]):
            if b_["x0"] - a_["x1"] < 0.5 * l["size"]: continue
            y0_, y1_ = int((l["top"] + 0.2 * (l["bottom"] - l["top"])) * s), int((l["bottom"] - 0.1 * (l["bottom"] - l["top"])) * s)
            x0_, x1_ = int(a_["x1"] * s) + 2, int(b_["x0"] * s) - 1
            if x1_ > x0_ and resto[y0_:y1_, x0_:x1_].sum() >= 12:
                l["tinta_meio"] = (a_["text"], b_["text"])
    # legenda ao lado da foto, alinhada com a base dela (ex.: "Barragem de Sobradinho – BA" na coluna de texto ao lado):
    # fica como texto, mas logo depois da figura
    for F in figs:
        f = F["bbox"]
        if F.get("alt") is not None: continue
        for l in linhas:
            if l.get("fig") is not None or l.get("em_par") or len(l["ws"]) > 8: continue
            t_l = txt_puro(l)
            if letra_alt(l) or RE_Q_NUM.match(t_l) or RE_Q_ENEM.match(t_l) or eh_cabecalho(l) is not None: continue
            if sum(1 for w in l["ws"] if re.search(r"[A-Za-zÀ-ú]{2,}", w["text"])) < 2: continue
            if os.environ.get("DEBUGF") and "Barragem" in txt_puro(l): print("  LEG?", [round(v) for v in f], round(l["x0"]), round(l["bottom"]), larg_col(l))
            if 0 <= l["x0"] - f[2] <= 25 and abs(l["bottom"] - f[3]) <= 8 and (l["x1"] - l["x0"]) < 0.55 * larg_col(l):
                l["legenda_de"] = id(f)
    return figs

TAB_EXPL = {}      # pagina -> [(caixa, ajustes)] de tabelas abertas (grade montada com fios explicitos)
def _fios(page):
    """fios finos da pagina (retangulos/linhas de ate 2 pt de espessura): (horizontais, verticais)"""
    hs, vs = [], []
    for o in list(page.rects) + list(page.lines):
        w_, h_ = o["x1"] - o["x0"], o["bottom"] - o["top"]
        if h_ <= 2 and w_ > 5: hs.append(o)
        elif w_ <= 2 and h_ > 5: vs.append(o)
    # fio horizontal desenhado em pedacos colados (um por coluna) vira um fio so
    hs = sorted(({"x0": h["x0"], "x1": h["x1"], "top": h["top"], "bottom": h["bottom"]} for h in hs), key=lambda h: (round(h["top"]), h["x0"]))
    uni = []
    for h in hs:
        u = uni[-1] if uni else None
        if u and abs(u["top"] - h["top"]) < 1.5 and h["x0"] <= u["x1"] + 2: u["x1"] = max(u["x1"], h["x1"])
        else: uni.append(dict(h))
    return uni, vs
def tabela_aberta(page, cab):
    """cab = faixa de cabecalho emoldurada (1 linha). Procura, logo abaixo, fio(s) vertical(is) interno(s) que descem
    da faixa ate um fio horizontal da mesma largura. Devolve a caixa da tabela inteira (e guarda a grade) ou None."""
    x0, y0, x1, y1 = cab
    if x1 - x0 < 100 or y1 - y0 > 30: return None
    hs, vs = _fios(page)
    seps = [v for v in vs if x0 + 10 < v["x0"] < x1 - 10 and abs(v["top"] - y1) < 3 and v["bottom"] - y1 >= 20]
    if not seps: return None
    fundo = [h for h in hs if h["x0"] <= x0 + 6 and h["x1"] >= x1 - 6 and y1 + 20 <= h["top"] <= y1 + 400
             and all(abs(h["top"] - v["bottom"]) < 4 for v in seps)]
    if not fundo: return None
    yb = min(fundo, key=lambda h: h["top"])["top"]
    xs = sorted({round(x0, 1), round(x1, 1)} | {round((v["x0"] + v["x1"]) / 2, 1) for v in seps})
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 8]
    aj = {"vertical_strategy": "explicit", "horizontal_strategy": "explicit",
          "explicit_vertical_lines": xs, "explicit_horizontal_lines": [y0, y1, yb]}
    try:
        t = page.extract_table(aj)
    except Exception:
        return None
    if not t or len(t) != 2 or any(not " ".join((c or "").split()) for c in t[0]): return None
    if sum(1 for c in t[1] if (c or "").strip()) < len(t[1]) - 0: return None
    cx = (x0, y0, x1, yb)
    TAB_EXPL.setdefault(page.page_number, []).append((cx, aj))
    return cx
def tabela(page, f):
    """Tenta transcrever uma figura como tabela (grade de linhas). So aceita se todo o texto couber nas celulas."""
    try:
        reg = page.crop((max(0, f[0] - 2), max(0, f[1] - 2), min(page.width, f[2] + 2), min(page.height, f[3] + 2)))
        if len(reg.lines) + len(reg.rects) < 4: return None
        aj = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
        for cx, aj_ in TAB_EXPL.get(page.page_number, []):
            if all(abs(a - b) < 3 for a, b in zip(cx, f)): aj = aj_
        tabs = reg.find_tables(aj)
        if len(tabs) != 1: return None
        tb = tabs[0].bbox
        if (tb[2] - tb[0]) * (tb[3] - tb[1]) < 0.8 * (f[2] - f[0]) * (f[3] - f[1]): return None   # tem foto/figura junto
        t = reg.extract_table(aj)
        if not t or len(t) < 2 or len(t[0]) < 2: return None
        cel = "".join("".join((c or "").split()) for r in t for c in r)
        tudo = "".join("".join(w["text"].split()) for w in reg.extract_words()
                       if tb[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= tb[2] + 1 and tb[1] - 1 <= (w["top"] + w["bottom"]) / 2 <= tb[3] + 1)
        fora = [w for w in reg.extract_words() if not (tb[0] - 1 <= (w["x0"] + w["x1"]) / 2 <= tb[2] + 1 and tb[1] - 1 <= (w["top"] + w["bottom"]) / 2 <= tb[3] + 1)
                and f[0] <= (w["x0"] + w["x1"]) / 2 <= f[2] and f[1] <= (w["top"] + w["bottom"]) / 2 <= f[3]]
        if fora: return None      # ha texto na figura fora da grade (legenda, rotulo de foto...)
        if sorted(cel) != sorted(tudo): return None
        if any(c is None for r in t for c in r): return None
        cab_curto_t = all(0 < len(" ".join((c or "").split())) <= 40 for c in t[0])
        if any(len(" ".join((c or "").split())) > 120 for r in t for c in r) and not cab_curto_t: return None   # caixa de layout, nao tabela de dados
        if reg.images: return None
        # celulas com formatacao (italico, negrito, expoente, indice), montadas com as palavras da pagina
        try:
            ws_pg = paginas[page.page_number - 1]["ws"]
            rows_ = tabs[0].rows
            if len(rows_) == len(t):
                t2 = []
                for r_, row in zip(t, rows_):
                    nova_r = []
                    for c_, cb in zip(r_, row.cells):
                        if cb is None: nova_r.append(c_); continue
                        wc = sorted([w for w in ws_pg if cb[0] - 0.5 <= (w["x0"] + w["x1"]) / 2 <= cb[2] + 0.5 and cb[1] - 0.5 <= (w["top"] + w["bottom"]) / 2 <= cb[3] + 0.5],
                                    key=lambda w: (round(w["top"] / 3), w["x0"]))
                        grupos_c = []
                        for w in wc:
                            if grupos_c and abs(grupos_c[-1][0]["top"] - w["top"]) < 0.5 * w["size"] or (grupos_c and (w["sup"] or w["sub"]) and w["top"] < grupos_c[-1][0]["bottom"] + 2):
                                grupos_c[-1].append(w)
                            else: grupos_c.append([w])
                        # item de lista dentro da celula ("- desenvolvido", "- pequena dimensao...") fica em linha propria
                        md_c = ""
                        for g_ in grupos_c:
                            t_g = md_linha({"ws": sorted(g_, key=lambda w: w["x0"])})
                            md_c += ("<br>" if md_c and re.match(r"^\s*[-–•▪]\s", t_g) else (" " if md_c else "")) + t_g
                        md_c = re.sub(r"(?<!\*)\*\* \*\*(?!\*)", " ", md_c)
                        plano = re.sub(r"<[^>]+>|\*", "", md_c)
                        nova_r.append(md_c if "".join(plano.split()) == "".join((c_ or "").split()) else c_)
                    t2.append(nova_r)
                t = t2
        except Exception:
            pass
        linhas = ["| " + " | ".join(" ".join((c or "").split()) for c in r) + " |" for r in t]
        linhas.insert(1, "|" + "---|" * len(t[0]))
        return "\n".join(linhas)
    except Exception:
        return None

# margem direita tipica do texto corrido (pagina menos a borda direita das linhas justificadas de largura total)
_x1s = [l["x1"] for pg in paginas for l in pg["linhas"] if abs(l["size"] - CORPO) < 0.6 and (l["col"][1] - l["col"][0]) > 0.8 * pg["page"].width]
_moda = collections.Counter(round(x) for x in _x1s).most_common(1)
_bt = collections.defaultdict(lambda: ([], []))
for pg in paginas:
    for l in pg["linhas"]:
        if abs(l["size"] - CORPO) < 0.6: _bt[(round(l["col"][0]), round(l["col"][1]))][0].append(round(l["x0"])); _bt[(round(l["col"][0]), round(l["col"][1]))][1].append(round(l["x1"]))
BORDA_TIPICA = {k: (collections.Counter(v[0]).most_common(1)[0][0], collections.Counter(v[1]).most_common(1)[0][0]) for k, v in _bt.items() if len(v[0]) >= 10}
MARGEM_DIR = (paginas[0]["page"].width - _moda[0][0]) if len(_x1s) > 20 else 40
# ------------------------------------------------------------------ formato da prova (reconhecido pelo codigo)
# Cada banca numera questoes e alternativas de um jeito. Em vez de um perfil por banca, o codigo mede na propria prova:
#  - estilo do cabecalho da questao: "QUESTAO 91" | "10. Texto..." | numero sozinho em negrito ("4", "01");
#    vence o estilo que forma a maior sequencia 1, 2, 3... (ou 91, 92...) na ordem das paginas;
#  - marcador de alternativa "A." (so vale se A., B., C., D. aparecem muitas vezes);
#  - numero de alternativas (4 ou 5): se quase nao ha "E", a prova tem 4 (a-d).
_ord_l = sorted(((pg["n"], round(l["col"][0]), l["top"], l) for pg in paginas for l in pg["linhas"]), key=lambda x: x[:3])
_pontos = collections.Counter(m.group(1) for *_, l in _ord_l for m in [re.match(r"^([A-E])\.(\s|$)", txt_puro(l))] if m)
ALT_PONTO = min(_pontos.get(k, 0) for k in "ABCD") >= 5 and max(_pontos.values()) <= 3 * min(_pontos.get(k, 0) for k in "ABCD")
def _cadeia(estilo):
    """maior sequencia n, n+1, n+2... de cabecalhos do estilo, com cada numero na mesma pagina ou depois do anterior
    (a ordem dentro da pagina nao importa: colunas e quadros mudam a ordem de leitura)"""
    cands = sorted({(n, pn_) for pn_, _, _, l in _ord_l for e, n in cand_cabecalho(l) if e == estilo})
    comp = {}; ini = {}; ant_ = {}
    for n, p_ in cands:
        ants = [(comp[(m, q)], q) for (m, q) in comp if m == n - 1 and q <= p_]
        if ants:
            c_, q = max(ants); comp[(n, p_)] = c_ + 1; ini[(n, p_)] = ini[(n - 1, q)]; ant_[(n, p_)] = (n - 1, q)
        else:
            comp[(n, p_)] = 1; ini[(n, p_)] = (n, p_)
    if not comp: return 0, None, set()
    fim = max(comp, key=lambda k: comp[k])
    caminho = set(); k_ = fim
    while k_ is not None:
        caminho.add(k_); k_ = ant_.get(k_)
    return comp[fim], ini[fim], caminho
_cad = {e: _cadeia(e) for e in ("questao", "ponto", "solto")}
if os.environ.get("DEBUGQ"):
    for pn_, _, _, l in _ord_l:
        if re.match(r"^\W*(QUEST|0?\d{1,3}\b)", txt_puro(l)): print("CAB?", pn_, txt_puro(l)[:30], cand_cabecalho(l), [w["bold"] for w in l["ws"][:2]], round(l["size"], 1))
ESTILO_Q = max(("questao", "ponto", "solto"), key=lambda e: (_cad[e][0], -("questao", "ponto", "solto").index(e)))
if _cad[ESTILO_Q][0] < 3: ESTILO_Q = None
# numero solto em negrito so e cabecalho se faz parte da sequencia (numero "1", "2" sob fotos nao e questao)
CAB_OK = _cad[ESTILO_Q][2] if ESTILO_Q == "solto" else None
PRIMEIRA_Q, PAG_Q1 = _cad[ESTILO_Q][1] if ESTILO_Q else (1, 1)
_letras = collections.Counter(letra_alt(l) for *_, l in _ord_l)
ULT_LETRA = "D" if _letras.get("D", 0) >= 5 and _letras.get("E", 0) < 0.3 * _letras.get("D", 0) else "E"
N_ALT = "ABCDE".index(ULT_LETRA) + 1
TEM_TEXTO_PARA = any(RE_TEXTO_PARA.match(txt_puro(l)) for *_, l in _ord_l)
if PERFIL == "auto":
    PERFIL = "enem" if ESTILO_Q == "questao" and not TEM_TEXTO_PARA else "ssa"
print(f"formato: cabeçalho={ESTILO_Q} (sequência de {_cad[ESTILO_Q][0] if ESTILO_Q else 0}, começa na {PRIMEIRA_Q}, pág. {PAG_Q1}), "
      f"alternativas={N_ALT}{' com A.' if ALT_PONTO else ''}, fluxo={PERFIL}, 'texto para as questões'={TEM_TEXTO_PARA}")
# codigo interno de questao (simulados): no cabecalho ("QUESTAO 95  R387") e na linha logo abaixo ("196SE02BIO2019II")
# nao e texto da questao: sai da linha / a linha sai da leitura (a tinta continua apagada, nao vira figura)
for pg in paginas:
    novas_ = []; cabs = []
    for l in pg["linhas"]:
        if eh_cabecalho(l) is not None:
            resto_ = [w for w in l["ws"] if not eh_codigo_tok(w["text"])
                      and not ((w["sub"] or w["sup"] or w["size"] < 0.8 * CORPO) and re.fullmatch(r"[A-Z0-9ØÇ_]{2,12}", w["text"]))]
            if len(resto_) < len(l["ws"]):
                l["ws"] = resto_; l["x0"] = min(w["x0"] for w in resto_); l["x1"] = max(w["x1"] for w in resto_)
            cabs.append(l)
    for l in pg["linhas"]:
        if all(eh_codigo_tok(w["text"]) for w in l["ws"]) and any(0 <= l["top"] - c["bottom"] < 2.5 * CORPO and l["col"] == c["col"] for c in cabs):
            continue
        # etiqueta/codigo ao lado ou logo abaixo do cabecalho ("QUESTAO 91 .... YUKD", "CALIBRADA MAT" em letra miuda):
        # so maiusculas/digitos, a direita do cabecalho ou em letra pequena
        if eh_cabecalho(l) is None and all(re.fullmatch(r"[A-Z0-9ØÇ_]{2,12}", w["text"]) or eh_codigo_tok(w["text"]) for w in l["ws"]) and len(l["ws"]) <= 3 and any(
                -0.5 * CORPO <= l["top"] - c["top"] < 2.5 * CORPO and l["col"] == c["col"] and (l["x0"] > c["x1"] + 10 or l["size"] < 0.8 * CORPO)
                for c in cabs):
            continue
        novas_.append(l)
    pg["linhas"] = novas_
    # linha feita so de simbolos soltos (pontos do braile "•  •", quadradinhos): e desenho, nao texto -> sai das
    # palavras e a tinta vira figura
    so_simb = [l for l in pg["linhas"] if all(re.fullmatch(r"[•●○◦▪■□·◆◇▲△▼▽★☆]+", w["text"]) for w in l["ws"])]
    if so_simb:
        ids_w = {id(w) for l in so_simb for w in l["ws"]}
        pg["linhas"] = [l for l in pg["linhas"] if l not in so_simb]
        pg["ws"] = [w for w in pg["ws"] if id(w) not in ids_w]
        # linhas de simbolos empilhadas (celula do braile em 3 linhas) = um desenho so
        grupos_s = []
        for l in sorted(so_simb, key=lambda l: l["top"]):
            g_ = grupos_s[-1] if grupos_s else None
            if g_ and l["top"] - g_[3] < 1.5 * l["size"] and min(l["x1"], g_[2]) - max(l["x0"], g_[0]) > -l["size"]:
                g_[0], g_[2], g_[3] = min(g_[0], l["x0"]), max(g_[2], l["x1"]), max(g_[3], l["bottom"])
            else:
                grupos_s.append([l["x0"], l["top"], l["x1"], l["bottom"]])
        FIG_FORCADA.setdefault(pg["n"], []).extend(grupos_s)
# paginas de redacao/instrucoes antes da 1a questao (propostas de redacao, "Texto 1" da redacao) nao sao texto-base
RE_REDACAO = re.compile(r"(?i)reda[çc][ãa]o|redija|dissertativ|voc[êe] dever[áa]|produ[çc][ãa]o de texto|proposta de|instru[çc][õo]es")
PAGS_FORA = {pg["n"] for pg in paginas if pg["n"] < PAG_Q1 and RE_REDACAO.search(" ".join(txt_puro(l) for l in pg["linhas"]))}
# capa com formulario do candidato ("DADOS DE IDENTIFICACAO DO CANDIDATO", "No de Inscricao") antes da 1a questao:
# e do caderno, nao de questao nenhuma (desde que a pagina nao traga um texto-base rotulado)
RE_CAPA = re.compile(r"(?i)identifica[çc][ãa]o do candidato|n[º°o.]*\s*de\s+inscri[çc][ãa]o|assinatura do candidato|nome do candidato")
PAGS_FORA |= {pg["n"] for pg in paginas if pg["n"] < PAG_Q1 and RE_CAPA.search(" ".join(txt_puro(l) for l in pg["linhas"]))
              and not any(re.match(r"(?i)^\W*texto\s+(\d{1,2}|[IVX]{1,4})\b", txt_puro(l)) for l in pg["linhas"])}
# proposta de redacao no meio/fim do caderno (pagina sem nenhuma questao): tambem fica fora
RE_REDACAO_FORTE = re.compile(r"(?i)proposta de reda[çc][ãa]o|instru[çc][õo]es para a reda[çc][ãa]o|folha de reda[çc][ãa]o|rascunho da reda[çc][ãa]o")
PAGS_FORA |= {pg["n"] for pg in paginas if pg["n"] > PAG_Q1 and not any(eh_cabecalho(l) is not None for l in pg["linhas"])
              and RE_REDACAO_FORTE.search(" ".join(txt_puro(l) for l in pg["linhas"]))}
# contracapa depois da ultima questao (restos de tabela de cores "1 Az / 2 Am", codigo de barras): sem nenhuma
# alternativa e sem nenhuma linha de texto corrido -> fora (senao os restos grudam na ultima alternativa)
_ult_cab = max([pg["n"] for pg in paginas if any(eh_cabecalho(l) is not None for l in pg["linhas"])] or [0])
PAGS_FORA |= {pg["n"] for pg in paginas if _ult_cab and pg["n"] > _ult_cab and not any(letra_alt(l) for l in pg["linhas"])
              and not any(len(l["ws"]) >= 5 for l in pg["linhas"])}
if PAGS_FORA: print("páginas de redação/instruções (fora do banco):", sorted(PAGS_FORA))

# ------------------------------------------------------------------ fluxo de leitura
itens = []   # na ordem de leitura: ("linha", l, pg, col) ou ("fig", bbox, pg, col)
nfig = 0
# figuras de todas as paginas primeiro: logotipo/enfeite que se repete no alto ou no pe de varias paginas
# (ex.: "SAS", "enem 2021") e cabecalho grafico, nao figura de questao
LOGOS = []
# a 1a passada (so para achar logotipos) mexe nas linhas (palavras dentro de figura saem da linha): guarda as linhas
# para a 2a passada comecar do zero (faixa decorativa da margem juntada a um infografico engolia as alternativas)
_LINHAS0 = {pg["n"]: [dict(l, ws=list(l["ws"])) for l in pg["linhas"]] for pg in paginas}
FIGS_PG = {pg["n"]: detecta_figuras(pg) for pg in paginas}
_chave_f = lambda b, H: (round(b[0] / 4), round(b[1] / 4), round(b[2] / 4), round(b[3] / 4)) if (b[1] < 0.12 * H or b[3] > 0.88 * H) else None
_rep_f = collections.Counter(k for pg in paginas for F in FIGS_PG[pg["n"]] for k in [_chave_f(F["bbox"], pg["page"].height)] if k)
if os.environ.get("DEBUGF"): print("FIGS REPETIDAS", _rep_f.most_common(6))
LOGOS = [[v * 4 - 2 for v in k[:2]] + [v * 4 + 2 for v in k[2:]] for k, c in _rep_f.items() if c >= max(3, 0.15 * NPAG)]
if LOGOS:
    print("logotipos/enfeites repetidos (fora das figuras):", len(LOGOS))
    for pg in paginas:
        # pagina com figura que contem o logotipo (juntou com ele) ou com o proprio logotipo: detecta de novo sem ele
        if any(any(F["bbox"][0] <= L_[2] and F["bbox"][2] >= L_[0] and F["bbox"][1] <= L_[3] and F["bbox"][3] >= L_[1] for L_ in LOGOS) for F in FIGS_PG[pg["n"]]):
            pg["linhas"] = [dict(l, ws=list(l["ws"])) for l in _LINHAS0[pg["n"]]]
            for l in pg["linhas"]: l.pop("fig", None)
            FIGS_PG[pg["n"]] = detecta_figuras(pg)
for pg in paginas:
    figs = FIGS_PG[pg["n"]]
    pg["figs_bb"] = [list(F["bbox"]) for F in figs]
    for l in pg["linhas"]:     # figura logo a direita da linha (texto que contorna a figura): limite da linha
        h_ = l["bottom"] - l["top"]
        dirs = [F["bbox"][0] for F in figs if min(l["bottom"], F["bbox"][3]) - max(l["top"], F["bbox"][1]) > 0.3 * h_ and F["bbox"][0] >= l["x1"] - 2
                and l["col"][0] <= F["bbox"][0] < l["col"][1]]
        if dirs: l["lim_dir"] = min(dirs)
    reg_fig = {}
    for F in figs:
        f = F["bbox"]
        if F["alt"] is not None: reg_fig[id(F)] = F["alt"]["reg"]; continue
        ovs = [max(0, min(f[2], r[1]) - max(f[0], r[0])) * max(0, min(f[3], r[3]) - max(f[1], r[2])) for r in pg["regs"]]
        reg_fig[id(F)] = max(range(len(ovs)), key=lambda k: ovs[k])
    for ri, (cx0, cx1, ry0, ry1) in enumerate(pg["regs"]):
        corpo_l = [l for l in pg["linhas"] if l["reg"] == ri and not l.get("pequena") and l.get("fig") is None]
        if len(corpo_l) >= 4:
            xs0 = sorted(l["x0"] for l in corpo_l); xs1 = sorted(l["x1"] for l in corpo_l)
            borda = (xs0[len(xs0) // 10], xs1[int(len(xs1) * 0.9)])
            # texto nao justificado (poema, letra de musica): a borda da direita e a da coluna, nao a da linha mais longa
            justif = sum(1 for x in xs1 if abs(x - borda[1]) < 2.5) >= 0.35 * len(xs1)
            # texto nao justificado (verso): cada grupo de linhas com a mesma borda direita (regiao inteira, ou linhas
            # ao lado de uma mesma figura) e testado; linhas de grupo "irregular" sao versos (quebra em toda linha)
            grupos_j = collections.defaultdict(list)
            for l_ in corpo_l: grupos_j[round(l_.get("lim_dir", 1e9))].append(l_)
            lim_col_ = cx1 - MARGEM_DIR if cx1 > pg["page"].width - 1 else cx1 - 8
            for k_g, g_ls in grupos_j.items():
                if len(g_ls) < 3: continue
                x1s_ = sorted(l_["x1"] for l_ in g_ls); p90_ = x1s_[int(len(x1s_) * 0.9)]
                lim_g = min(lim_col_, k_g - 4) if k_g < 1e8 else lim_col_
                chegam = sum(1 for x in x1s_ if x > lim_g - 12)        # linhas que vao ate a borda (prosa)
                if sum(1 for x in x1s_ if abs(x - p90_) < 2.5) < 0.35 * len(x1s_) and chegam <= 0.2 * len(x1s_):
                    for l_ in g_ls: l_["irregular"] = True

        else:
            # poucas linhas na regiao: usa as bordas tipicas de regioes iguais no resto da prova
            borda = BORDA_TIPICA.get((round(cx0), round(cx1)), (cx0 + 30, cx1 - 30))
        bloc = []
        ids_figs = {id(F["bbox"]) for F in figs}
        for l in pg["linhas"]:
            if l.get("fig") is not None: continue
            if l.get("legenda_de") in ids_figs: continue          # legenda vai junto com a figura dela
            if l["reg"] == ri: bloc.append((l["top"], "linha", l))
        for F in figs:
            if reg_fig[id(F)] == ri:
                chave = F["alt"]["top"] + 0.01 if F["alt"] is not None else F["bbox"][1] - 0.5
                if F["alt"] is None:
                    # figura ao lado do texto (imagem a esquerda, texto a direita): entra antes do texto que esta ao lado
                    fb = F["bbox"]
                    lado = [l for l in pg["linhas"] if l["reg"] == ri and l.get("fig") is None
                            and min(l["bottom"], fb[3]) - max(l["top"], fb[1]) > 0 and (l["x0"] >= fb[2] - 2 or l["x1"] <= fb[0] + 2)]
                    if lado:
                        if all(l["x0"] >= fb[2] - 2 for l in lado):      # imagem a esquerda: vem antes do texto ao lado
                            prim = min(lado, key=lambda l: l["top"])
                            inicio_q = RE_Q_NUM.match(txt_puro(prim)) or RE_Q_ENEM.match(txt_puro(prim)) or eh_cabecalho(prim) is not None
                            chave = prim["top"] + 0.5 if inicio_q else min(chave, prim["top"] - 0.5)
                        else:                                             # imagem a direita: vem depois do enunciado ao lado, antes das alternativas
                            alts_l = [l for l in lado if letra_alt(l)]
                            chave = (min(l["top"] for l in alts_l) - 0.5) if alts_l else (max(l["top"] for l in lado) + 0.5)
                bloc.append((chave, "fig", F["bbox"]))
                for l in pg["linhas"]:
                    if l.get("legenda_de") == id(F["bbox"]) and l.get("fig") is None:
                        bloc.append((chave + 0.001, "linha", l))
        # empate de posicao: o cabecalho da questao vem antes da figura que comeca na mesma altura
        cabs_b = [o for _, t_, o in bloc if t_ == "linha" and eh_cabecalho(o) is not None]
        def chave_b(x):
            if x[1] == "fig":
                # figura que comeca na altura de um cabecalho de questao (cresceu ate a faixa ao lado dele): vem depois dele
                for c_ in cabs_b:
                    if abs(c_["top"] - x[2][1]) < 4 and min(c_["x1"], x[2][2]) - max(c_["x0"], x[2][0]) > -15:
                        return (max(x[0], c_["top"]) + 0.001, 1)
            return (x[0], 0 if x[1] == "linha" and eh_cabecalho(x[2]) is not None else 1)
        for _, tipo, obj in sorted(bloc, key=chave_b):
            itens.append({"tipo": tipo, "obj": obj, "pg": pg["n"], "col": (cx0, cx1), "borda": borda,
                          "lim_col": (cx1 - MARGEM_DIR if cx1 > pg["page"].width - 1 else cx1 - 8)})

def texto_na_uniao(A, B, pn):
    """a caixa que junta as figuras A e B cobre texto corrido que nao e de nenhuma das duas"""
    U = (min(A[0], B[0]), min(A[1], B[1]), max(A[2], B[2]), max(A[3], B[3]))
    den = lambda F, l: F[0] - 1 <= (l["x0"] + l["x1"]) / 2 <= F[2] + 1 and F[1] - 1 <= (l["top"] + l["bottom"]) / 2 <= F[3] + 1
    return any(l.get("fig") is None and len(l["ws"]) >= 3 and den(U, l) and not den(A, l) and not den(B, l)
               for l in paginas[pn - 1]["linhas"])
def marcador_abaixo(F, pn):
    """letra de alternativa ("(B)") logo abaixo da figura e centrada nela"""
    for l in paginas[pn - 1]["linhas"]:
        for i_w, w in enumerate(l["ws"]):
            prox_w = l["ws"][i_w + 1] if i_w + 1 < len(l["ws"]) else None
            vazio = prox_w is None or re.fullmatch(r"\(?[a-eA-E]\)", prox_w["text"]) is not None   # "(B)" sem texto depois
            if vazio and re.fullmatch(r"\(?[a-eA-E]\)", w["text"]) and F[3] - 4 <= w["top"] <= F[3] + 18 and F[0] - 5 <= (w["x0"] + w["x1"]) / 2 <= F[2] + 5:
                return True
    return False
# ------------------------------------------------------------------ dono geometrico de cada item
# O que marca a divisao entre questoes e o cabecalho ("QUESTAO 22", "———— 22", caixa "22"): tudo o que esta abaixo
# dele, na mesma coluna, e da questao, ate o proximo cabecalho. Quando a ordem de leitura intercala pedacos de duas
# questoes (ex.: tabela a esquerda e texto a direita dentro da mesma questao, ENEM 2005), os itens sao reagrupados
# pelo cabecalho que esta logo acima deles. Item sem cabecalho acima na mesma coluna continua com o dono do item anterior.
if ESTILO_Q is not None:
    def _sobrepoe(a_, b_):
        return min(a_[1], b_[1]) - max(a_[0], b_[0]) > 0.5 * min(a_[1] - a_[0], b_[1] - b_[0])
    novos_itens = []
    for pn_ in sorted({it["pg"] for it in itens}):
        its = [it for it in itens if it["pg"] == pn_]
        cabs_p = [(k_, it) for k_, it in enumerate(its) if it["tipo"] == "linha" and eh_cabecalho(it["obj"]) is not None]
        if not cabs_p:
            novos_itens += its; continue
        dono = None; chaves = []
        for k_, it in enumerate(its):
            # figura: vale a altura de um pouco abaixo do topo (a figura ao lado do cabecalho comeca na mesma altura dele)
            top_ = it["obj"]["top"] if it["tipo"] == "linha" else it["obj"][1] + min(20, 0.3 * (it["obj"][3] - it["obj"][1]))
            cands_ = [(c_["obj"]["top"], kc) for kc, c_ in cabs_p if c_["obj"]["top"] <= top_ + 1 and _sobrepoe(c_["col"], it["col"])]
            if cands_:
                t_c, k_c = max(cands_)
                # outro cabecalho (de outra coluna) entre o cabecalho candidato e o item: o candidato nao alcanca o item;
                # fica a ordem de leitura (continuacao da questao anterior na leitura)
                if not any(t_c < c_["obj"]["top"] <= top_ + 1 for kc, c_ in cabs_p if kc != k_c):
                    dono = k_c
            if not cands_ and it["tipo"] == "fig":
                # figura no alto de outra coluna, sem cabecalho acima dela, lado a lado com uma figura ja lida (par de
                # figuras "Maior afastamento | Maior aproximacao" do texto-base): fica junto dessa figura
                F_ = it["obj"]
                irma = [k2 for k2 in range(k_) if its[k2]["tipo"] == "fig" and not _sobrepoe(its[k2]["col"], it["col"])
                        and abs(its[k2]["obj"][1] - F_[1]) < 6 and abs(its[k2]["obj"][3] - F_[3]) < 0.2 * (F_[3] - F_[1]) + 6]     # mesmo topo, mesma altura
                if irma:
                    c2 = chaves[irma[-1]]
                    chaves.append((c2[0], c2[1], irma[-1] + 0.5, k_)); continue
            chaves.append((-1 if dono is None else dono, 0 if (it["tipo"] == "linha" and k_ == dono) else 1, k_, k_))
        mudou = [c_[3] for c_ in sorted(chaves)] != list(range(len(its)))
        if mudou and os.environ.get("DEBUGDONO"): print("reagrupado pelo cabecalho: pág.", pn_)
        novos_itens += [its[c_[3]] for c_ in sorted(chaves)]
    itens = novos_itens

# ------------------------------------------------------------------ segmentacao em questoes
RE_ALT_SSA = re.compile(r"^\(?([a-eA-E])\)\s*")
RE_FONTE = re.compile(r"(?i)(dispon[ií]vel em|disponible en|available (at|in|from)|acceso|accessed|retrieved|fuente:|source:|acesso em|adaptado|fragmento|in:|editora|revista|jornal|\b(19|20)\d\d\b|[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,},\s+[A-Z]\.)")

if os.environ.get("ORDEM"):
    for it in itens:
        if it["pg"] in [int(x) for x in os.environ["ORDEM"].split(",")]:
            o = it["obj"]
            print(it["pg"], it["tipo"], round(o["top"] if it["tipo"] == "linha" else o[1]), it["col"], (txt_puro(o)[:60] if it["tipo"] == "linha" else [round(v) for v in o]))
RE_FAIXA = re.compile(r"(?i)quest\w*\s*(?:de\s*)?0*(\d{1,3})\s*(?:a|-|–)\s*0*(\d{1,3})")
questoes = []; textos_base = []; atual = None; base_atual = None; esperado = None; area = ""
iniciou = False; ult_linha = None; ult_it = None
idioma = None; faixa_idioma = None; max_num = 0
def novo_bloco():
    return {"partes": [], "paginas": set(), "caixas": collections.defaultdict(list)}

ordem_idioma = []; passagem = 0
def idioma_de(n):
    if not (faixa_idioma and faixa_idioma[0] <= n <= faixa_idioma[1] and ordem_idioma): return None
    return ordem_idioma[min(passagem, len(ordem_idioma) - 1)]

def com_seguinte(i_):
    """texto da linha i_ + a linha seguinte (rotulo que quebra em 2 linhas: "...para responder as questoes / de 14 a 16.")"""
    t_ = txt_puro(itens[i_]["obj"]).strip()
    if i_ + 1 < len(itens) and itens[i_ + 1]["tipo"] == "linha" and itens[i_ + 1]["pg"] == itens[i_]["pg"]:
        t_ += " " + txt_puro(itens[i_ + 1]["obj"]).strip()
    return t_
RE_INICIO_ROTULO = re.compile(r"(?i)^\W*(observe|leia|considere|analise|examine|texto|textos|com base|baseie|para (as|a) quest|(as|a) quest\w*\s+\d|read|the following|lea)\b")
def rotulo_de(i_):
    """faixa de questoes se a linha i_ comeca um rotulo de texto-base, senao None"""
    t_ = txt_puro(itens[i_]["obj"]).strip()
    mm_ = RE_TEXTO_PARA.match(t_)
    if mm_: return [int(x) for x in re.findall(r"\d{1,3}", mm_.group(3))]
    if RE_INICIO_ROTULO.match(t_): return rotulo_faixa(com_seguinte(i_))
    return None
for i_it, it in enumerate(itens):
    if it["pg"] in PAGS_FORA:       # redacao/instrucoes antes da 1a questao
        if it["tipo"] == "linha": it["obj"]["uso"] = "redação/instruções"
        continue
    if it["tipo"] == "linha":
        l = it["obj"]; t = txt_puro(l).strip()
        negrito = all(w["bold"] for w in l["ws"])
        if re.fullmatch(r"(?i)\W*(espa[çc]o\s+(reservado\s+)?(para|de)\s+)?rascunho\W*", t):
            l["uso"] = "rascunho"; continue          # area de rascunho do caderno: nao e conteudo
        # 2a linha de um titulo de area ("LINGUAGENS, CODIGOS E SUAS" / "TECNOLOGIAS"): continua sendo titulo
        if (negrito and ult_linha is not None and ult_linha.get("uso") == "titulo de area" and ult_it["pg"] == it["pg"]
                and 0 <= l["top"] - ult_linha["bottom"] < 1.2 * CORPO and re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ ,]+", t) and len(t) < 50
                and eh_cabecalho(l) is None):
            l["uso"] = "titulo de area"; ult_linha, ult_it = l, it; continue
        mi = RE_IDIOMA.search(t)
        if mi:
            idioma = "inglês" if mi.group(5).lower().startswith("ingl") else "espanhol"
            if not ordem_idioma: ordem_idioma[:] = [idioma, "espanhol" if idioma == "inglês" else "inglês"]
            mf = RE_FAIXA.search(t)
            if mf: faixa_idioma = (int(mf.group(1)), int(mf.group(2)))
            if len(t) < 90 and (PERFIL == "enem" or iniciou):
                l["uso"] = "instrucao de idioma"; ult_linha, ult_it = l, it; continue       # linha de instrucao ("Questoes de 20 a 23 (Opcao Espanhol)")
        n_cab = eh_cabecalho(l)
        if PERFIL == "enem" and n_cab is not None:
            n = n_cab; m = RE_Q_ENEM.match(t)
            if faixa_idioma and not (faixa_idioma[0] <= n <= faixa_idioma[1]): idioma = None
            atual = {"numero": n, "area": area, "idioma": (idioma if faixa_idioma and faixa_idioma[0] <= n <= faixa_idioma[1] else None), **novo_bloco()}
            questoes.append(atual); base_atual = None
            atual["caixas"][it["pg"]].append([l["x0"], l["top"], l["x1"], l["bottom"]])
            resto = t[m.end():].strip() if m else ""
            if resto: atual["partes"].append(("linha", l, it, True))
            else: l["uso"] = "cabecalho da questao"
            continue
        if PERFIL == "ssa":
            if not iniciou:
                if re.match(r"(?i)^texto\s*0?1\b|^texto para", t) or eh_cabecalho(l) == PRIMEIRA_Q or (rotulo_de(i_it) or [0])[0] == PRIMEIRA_Q:
                    iniciou = True
                elif negrito and RE_AREA.match(t):
                    # o 1o titulo de area ("LINGUAGENS...", "Questoes de 01 a 23") marca o inicio do conteudo:
                    # o texto de introducao que vem antes do "Texto 1" nao pode ser perdido
                    iniciou = True
                    if not t.lower().startswith("quest"): area = t
                    l["uso"] = "titulo de area"; ult_linha, ult_it = l, it
                    continue
                else:
                    l["uso"] = "antes do início das questões (capa/instruções)"
                    continue
            n_cab = eh_cabecalho(l)
            if n_cab is not None:
                n = n_cab
                recomeco = faixa_idioma is not None and n == faixa_idioma[0] and esperado == faixa_idioma[1] + 1
                if recomeco: passagem += 1
                if (esperado is None and n == PRIMEIRA_Q) or n == esperado or recomeco:
                    atual = {"numero": n, "area": area, "idioma": idioma_de(n), **novo_bloco()}; questoes.append(atual); esperado = n + 1
                    atual["base_ref"] = base_atual["id"] if base_atual is not None and not base_atual.get("congelado") and base_atual["partes"] else None
                    if base_atual is not None: base_atual["congelado"] = True
                    if re.fullmatch(r"((?i:quest[ãa]o)\s+)?0*\d{1,3}\s*[.)–-]?", t): l["uso"] = "cabecalho da questao"   # so o numero
                    else: atual["partes"].append(("linha", l, it, "remove_num"))
                    atual["caixas"][it["pg"]].append([l["x0"], l["top"], l["x1"], l["bottom"]])
                    ult_linha = l; continue
            ma = letra_alt(l)
            if atual is not None and not atual.get("fechada"):
                if ma: atual["ult_alt"] = ma.lower()
                elif atual.get("ult_alt") == ULT_LETRA.lower():
                    # depois da alternativa e): linha colada = continuacao; linha afastada = fim da questao
                    mesma = ult_linha is not None and ult_it["pg"] == it["pg"] and ult_it["col"] == it["col"]
                    # alternativa que continua no alto da coluna/pagina seguinte (comeca com minuscula, a anterior sem ponto final)
                    continua = (not mesma and ult_linha is not None and t[:1].islower()
                                and not re.search(r"[.!?;)”\"]$", txt_puro(ult_linha).strip()))
                    eh_rotulo = bool(rotulo_de(i_it) or re.match(r"(?i)^\W*texto\s*(\d|[IVX]+\b)", t)
                                     # instrucao curta que abre o texto da questao seguinte ("Leia estes poemas.", "Observe a charge:")
                                     or (RE_INICIO_ROTULO.match(t) and len(t) < 80 and re.search(r"[.:]\W*$", t) and not letra_alt(l)))
                    if continua: pass
                    elif ESTILO_Q in ("questao", "solto") and not eh_rotulo:
                        # prova com cabecalho de questao explicito (caixa "07", "QUESTAO 7"): o que vem depois das
                        # alternativas e antes do proximo cabecalho e da questao ("Note e adote", dados, figura),
                        # a nao ser que seja um texto rotulado para outras questoes ("TEXTO PARA AS QUESTOES...")
                        pass
                    elif not mesma or l["top"] - ult_linha["bottom"] > 0.9 * CORPO:
                        atual["fechada"] = True
                    if eh_rotulo: atual["fechada"] = True
            if (atual is None or atual.get("fechada")) and negrito and RE_AREA.match(t):
                if not t.lower().startswith("quest"): area = t
                l["uso"] = "titulo de area"; ult_linha, ult_it = l, it
                continue
            if atual is None or atual.get("fechada"):
                if base_atual is None or base_atual.get("congelado"):
                    base_atual = {"id": f"{PID}-T{len(textos_base) + 1}", "apos": len(questoes) - 1, **novo_bloco()}
                    textos_base.append(base_atual)
                nums = rotulo_de(i_it)
                if nums:
                    if any(p[0] == "linha" for p in base_atual["partes"]):
                        base_atual["congelado"] = True     # novo texto comeca aqui
                        base_atual = {"id": f"{PID}-T{len(textos_base) + 1}", "apos": len(questoes) - 1, **novo_bloco()}; textos_base.append(base_atual)
                    faixa = (min(nums), max(nums))
                    base_atual["faixa"] = faixa; base_atual["idioma"] = idioma if (idioma and faixa_idioma and faixa_idioma[0] <= faixa[0] <= faixa_idioma[1]) else None
                base_atual["partes"].append(("linha", l, it, False))
                base_atual["caixas"][it["pg"]].append([l["x0"], l["top"], l["x1"], l["bottom"]])
                ult_linha, ult_it = l, it
                continue
        if RE_AREA.match(t) and negrito and (atual is None or PERFIL == "enem"):
            # "Questoes de 136 a 180" (faixa de questoes do bloco) e titulo de secao: nunca faz parte da questao
            if atual is None or not atual["partes"] or re.match(r"(?i)^quest[õo]es\s+de\s+\d+\s+a\s+\d+\W*(\([^)]*\))?\W*$", t) or \
                    PERFIL == "enem" and re.match(r"(?i)^(CI[ÊE]NCIAS|MATEM|LINGUAGENS)", t) and l["size"] >= CORPO:
                area = t if not t.lower().startswith("quest") else area
                l["uso"] = "titulo de area"; ult_linha, ult_it = l, it
                continue
        if atual is not None:
            atual["partes"].append(("linha", l, it, False))
            atual["caixas"][it["pg"]].append([l["x0"], l["top"], l["x1"], l["bottom"]])
        ult_linha, ult_it = l, it
    else:
        f = it["obj"]
        if PERFIL == "ssa" and not iniciou: continue
        if PERFIL == "ssa" and (atual is None or atual.get("fechada")) and (base_atual is None or base_atual.get("congelado")):
            base_atual = {"id": f"{PID}-T{len(textos_base) + 1}", "apos": len(questoes) - 1, **novo_bloco()}; textos_base.append(base_atual)
        alvo = atual if atual is not None and not atual.get("fechada") else base_atual
        if alvo is not None:
            ant = alvo["partes"][-1] if alvo["partes"] else None
            g0 = ant[1] if ant is not None and ant[0] == "fig" else None
            if (g0 is not None and ant[2]["pg"] == it["pg"] and ant[2]["col"] == it["col"] and f[1] - g0[3] < 3 * CORPO
                    and min(g0[2], f[2]) - max(g0[0], f[0]) > -20
                    and not tabela(paginas[it["pg"] - 1]["page"], g0) and not tabela(paginas[it["pg"] - 1]["page"], f)
                    and not (marcador_abaixo(g0, it["pg"]) and marcador_abaixo(f, it["pg"]))     # cada foto com a sua letra: separadas
                    and not texto_na_uniao(g0, f, it["pg"])):     # o recorte unico engoliria texto (enunciado ao lado)
                # figura logo depois de outra, sem texto no meio: e a mesma ilustracao -> um recorte so
                g = ant[1]
                g[0], g[1], g[2], g[3] = min(g[0], f[0]), min(g[1], f[1]), max(g[2], f[2]), max(g[3], f[3])
                alvo["caixas"][it["pg"]].append(list(f))
            else:
                alvo["partes"].append(("fig", f, it, False)); alvo["caixas"][it["pg"]].append(list(f))

# ------------------------------------------------------------------ montagem do markdown
def salva_fig(f, pn, nome):
    s = DPI_FIG / 72; m = 3
    # nao invade a figura vizinha (ex.: graficos de alternativas empilhados)
    f = list(f)
    dentro_de_f = lambda G: G[0] >= f[0] - 1 and G[2] <= f[2] + 1 and G[1] >= f[1] - 1 and G[3] <= f[3] + 1
    for G in paginas[pn - 1].get("figs_bb", []):
        if G == f or dentro_de_f(G) or not (min(f[2], G[2]) - max(f[0], G[0]) > 0): continue
        if f[1] < G[1] < f[3] and G[1] > (f[1] + f[3]) / 2: f[3] = min(f[3], G[1] - 0.5)
        elif f[1] < G[3] < f[3] and G[3] < (f[1] + f[3]) / 2: f[1] = max(f[1], G[3] + 0.5)
    # margem de 3 pt, menos onde ha texto de fora colado (para nao aparecer um pedaco de letra na borda)
    ws_p = [w for w in paginas[pn - 1]["ws"] if not (f[0] <= (w["x0"] + w["x1"]) / 2 <= f[2] and f[1] <= (w["top"] + w["bottom"]) / 2 <= f[3])]
    outras = [G for G in paginas[pn - 1].get("figs_bb", []) if G != f and not dentro_de_f(G)]
    def livre(x0, y0, x1, y1): return not any(w["x1"] > x0 and w["x0"] < x1 and w["bottom"] > y0 and w["top"] < y1 for w in ws_p) \
        and not any(G[2] > x0 and G[0] < x1 and G[3] > y0 and G[1] < y1 for G in outras)
    mt = m if livre(f[0], f[1] - m, f[2], f[1]) else 1
    mb = m if livre(f[0], f[3], f[2], f[3] + m) else 1
    ml = m if livre(f[0] - m, f[1], f[0], f[3]) else 1
    mr = m if livre(f[2], f[1], f[2] + m, f[3]) else 1
    x, y = (f[0] - ml) * s, (f[1] - mt) * s
    w, h = (f[2] - f[0] + ml + mr) * s, (f[3] - f[1] + mt + mb) * s
    arq = render(pn, DPI_FIG, x, y, w, h, "png", os.path.join(OUT, "img", nome))
    # texto da pagina que encosta no recorte mas NAO e da figura: guardado para ser apagado do recorte depois, se esse
    # texto sair como texto na questao (senao apareceria duas vezes; ex.: fonte de uma foto no recorte de duas fotos)
    pg_ = paginas[pn - 1]
    fotos = [(im["x0"], im["top"], im["x1"], im["bottom"]) for im in pg_["page"].images]
    cand = []
    X0c, Y0c, X1c, Y1c = f[0] - ml, f[1] - mt, f[2] + mr, f[3] + mb
    for l in pg_["linhas"]:
        if l.get("fig") is not None: continue
        bxs = []
        for w_ in l["ws"]:
            bx = w_.get("caixa") or (w_["x0"], w_["top"], w_["x1"], w_["bottom"])
            if bx[2] < X0c or bx[0] > X1c or bx[3] < Y0c or bx[1] > Y1c: continue
            cx_, cy_ = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
            if any(a_[0] <= cx_ <= a_[2] and a_[1] <= cy_ <= a_[3] for a_ in fotos): continue
            bxs.append(bx)
        if bxs: cand.append((bxs, txt_puro(l)))
    if cand: BRANCO[arq] = (cand, (X0c, Y0c), s)
    return os.path.relpath(arq, OUT)

RE_ITEM = re.compile(r"^\s*(?:(?:[IVX]{1,4}|\d{1,2})\s*[-–.)]|\((?:[IVX]{1,4}|\d{1,2})\)|[•▪●○])\s+")
def monta(bloco, prefixo, eh_questao):
    alertas = []; enun = []; fontes = []; alts = []; imagens = []
    par = ""; prev = None; alt_atual = None; ant_curta = False   # ant_curta: a linha anterior a prev tambem era curta (verso)
    figs_alt = []      # (id, pagina, caixa, alternativa corrente) das figuras que aparecem na parte das alternativas
    marcada = []       # alternativa marcada no caderno (circulo cheio na letra)
    figs_inicio = []; adiadas = set(); ignora_gap = False    # figuras tiradas do meio da frase: vao antes do enunciado
    x_item = None      # recuo pendente do item de lista em curso (I -, II -, 1., •)
    pos_alt = None     # bloco que vem depois da ultima alternativa ("Note e adote", dados): vai para antes do comando
    def destino():
        if pos_alt is not None: return pos_alt
        return alt_atual["md"] if alt_atual is not None else enun
    def flush():
        nonlocal par
        if par.strip(): destino().append(par.strip())
        par = ""
    ult_linha_fonte = {}     # indice da fonte -> ultima linha dela (para juntar continuacoes pela posicao)
    partes_ = bloco["partes"]
    for i_parte, (tipo, obj, it, flag) in enumerate(partes_):
        if tipo == "fig":
            if alt_atual is not None and alt_atual["letra"] == "E" and (alt_atual["md"] or par.strip()):
                pg_e = alt_atual.get("pg")
                if pg_e != it["pg"] or ((obj[2] - obj[0]) < 25 and (obj[3] - obj[1]) < 25):
                    alertas.append(f"figura na pág. {it['pg']} depois da alternativa E foi descartada (não faz parte da questão) — conferir")
                    continue
            # figura no meio de uma frase (texto que contorna a figura, figura ao lado de um item): nao corta o texto;
            # a figura vai para antes do enunciado
            fim_par = re.sub(r"[*_\s]+$", "", par)
            prox_l = next((p_ for p_ in partes_[i_parte + 1:] if p_[0] == "linha"), None)
            continua_ = prox_l is not None and re.match(r"^[\W\d]*[a-zà-ú]", txt_puro(prox_l[1])) is not None and not letra_alt(prox_l[1])
            meio_frase = eh_questao and alt_atual is None and pos_alt is None and fim_par and not re.search(r"[.:!?;)”\"»]$", fim_par) and continua_
            if not meio_frase: flush()
            pg = paginas[it["pg"] - 1]
            tb = None if meio_frase else tabela(pg["page"], obj)
            if tb:
                destino().append(tb); alertas.append("tabela transcrita automaticamente — conferir"); prev = None; continue
            k = len(imagens) + 1
            arq = salva_fig(obj, it["pg"], f"{prefixo}_img{k}")
            imagens.append({"id": k, "arquivo": arq, "pagina": it["pg"], "bbox": [round(v, 1) for v in obj]})
            if alt_atual is not None and pos_alt is None:
                figs_alt.append((k, it["pg"], obj, alt_atual))     # figura de alternativa: lugar decidido pela posicao (no fim)
            elif meio_frase:
                figs_inicio.append(f"{{{{img:{k}}}}}"); adiadas.add(id(obj)); ignora_gap = True
            else:
                destino().append(f"{{{{img:{k}}}}}")
            if (it["pg"], tuple(round(v, 1) for v in obj)) in TEXTO_EM_FIG:
                alertas.append(f"imagem {k} tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto")
            if (it["pg"], tuple(round(v, 1) for v in obj)) in CORTADAS:
                alertas.append(f"imagem {k} pode estar cortada (o desenho continua fora do recorte) — conferir")
            if (obj[2] - obj[0]) < 60 and (obj[3] - obj[1]) < 25:
                alertas.append(f"imagem {k} é pequena (pode ser fórmula ou símbolo no meio do texto) — conferir a posição")
            if not meio_frase: prev = None
            continue
        l = obj; l["uso"] = "texto"
        if re.search(r"[-�\x00-\x08\x0b\x0c\x0e-\x1f]", txt_puro(l)) and not any(txt_puro(l)[:40] in a_ for a_ in alertas):
            # caractere que a fonte nao traduz (pedaco de chave/parentese grande de sistema, sinal de formula em fonte
            # de simbolos): aparece como quadradinho -> a formula e transcrita lendo a imagem (digitada, nunca foto)
            alertas.append("PENDENTE: há um trecho desenhado (caractere que o PDF não traduz: chave, parêntese grande ou sinal de fórmula) na linha “%s” — transcrever lendo a imagem" % txt_puro(l)[:40])
        if any(w.get("t3f") == 2 for w in l["ws"]):
            # formula montada com glifos-imagem (letras de formula, sobrelinha, raiz, expoente): nao da para garantir
            # a montagem automatica -> transcricao lendo a imagem
            alertas.append("PENDENTE: há um trecho desenhado (fórmula em glifos-imagem, fonte Type3) na linha “%s” — transcrever lendo a imagem" % txt_puro(l)[:70])
        elif any(w.get("t3f") for w in l["ws"]) and not any("glifos" in a_ for a_ in alertas):
            alertas.append("símbolos lidos de glifos-imagem do PDF (fonte Type3: ×, ≈, sinais) — conferir com a página")
        if l.get("cid"):
            alertas.append("PENDENTE: há um trecho desenhado (símbolo que o PDF não traduz) na linha “%s” — transcrever lendo a imagem" % txt_puro(l)[:70])
        if l.get("tinta_meio"):
            alertas.append("PENDENTE: há um trecho desenhado (sem texto no PDF) entre “%s” e “%s” na linha “%s” — transcrever lendo a imagem" % (l["tinta_meio"][0], l["tinta_meio"][1], txt_puro(l)[:70]))
        md = md_linha(l)
        if flag == "remove_num": md = re.sub(r"^\**((?i:quest[ãa]o)\s+)?0*\d{1,3}\s*[.)–-]?\s*\**\s*", "", md, count=1)
        if flag is True and PERFIL == "enem": md = re.sub(r"^\**(?i:quest[ãa]o)\s+\d+\**\s*", "", md)
        pl = l["ws"][0]
        # varias alternativas na mesma linha (grade "a) [fig]   b) [fig]   c) [fig]"): uma alternativa por marcador
        if eh_questao and pos_alt is None:
            ws_o = sorted(l["ws"], key=lambda w: w["x0"])
            marc_i = [k_ for k_, w in enumerate(ws_o) if re.fullmatch(r"\(?[a-eA-E]\)", w["text"]) or (eh_bolinha(w["fontname"]) and re.fullmatch(r"([A-Ea-e])\1?", w["text"]))]
            letras_m = [re.sub(r"[^A-Ea-e]", "", ws_o[k_]["text"])[:1].upper() for k_ in marc_i]
            esperada = chr(ord(alts[-1]["letra"]) + 1) if alts else "A"
            if len(marc_i) >= 2 and marc_i[0] == 0 and letras_m == [chr(ord(esperada) + j_) for j_ in range(len(marc_i))] and \
                    all(ws_o[b_]["x0"] - ws_o[b_ - 1]["x1"] > 2 * l["size"] for b_ in marc_i[1:]):
                flush()
                for j_, k_ in enumerate(marc_i):
                    fim_ = marc_i[j_ + 1] if j_ + 1 < len(marc_i) else len(ws_o)
                    pedaco = ws_o[k_ + 1:fim_]
                    alt_atual = {"letra": letras_m[j_], "md": [], "pg": it["pg"], "pos": (it["pg"], ws_o[k_]["x0"], ws_o[k_]["top"])}
                    alts.append(alt_atual)
                    if pedaco: alt_atual["md"].append(md_linha({"ws": pedaco}))
                prev = l; par = ""; continue
        # alternativa?
        letra = None
        if eh_questao:
            if eh_bolinha(pl["fontname"]) and re.fullmatch(r"([A-Ea-e])\1?", pl["text"]):
                letra = pl["text"][0].upper(); md = md_linha({"ws": l["ws"][1:]}) if len(l["ws"]) > 1 else ""
            else:
                la = letra_alt(l)
                if la and (alt_atual is not None or la == "A") and (not alts or ord(la) == ord(alts[-1]["letra"]) + 1):
                    letra = la; md = re.sub(r"^\**\(?[a-eA-E][).]\**\s*", "", md)
        if letra:
            flush(); alt_atual = {"letra": letra, "md": [], "pg": it["pg"], "pos": (it["pg"], pl["x0"], pl["top"])}; alts.append(alt_atual); par = md; prev = l
            marcada.append((GAB_RAZAO.get((it["pg"], round(l["ws"][0]["top"])), 0), letra))
            continue
        # fonte / citacao (fonte pequena)
        if l.get("pequena") or l["size"] < 0.85 * CORPO:
            t = txt_puro(l)
            # referencia no estilo "Autor. *Obra*, 260-265." (letra pequena, com titulo em italico ou numero)
            ref = re.match(r"^[A-ZÁÉÍÓÚÂÊÔ][\wÀ-ú\-]+(\s[A-ZÁÉÍÓÚÂÊÔ][\wÀ-ú\-]+)*[.,]\s", t) and (any(w.get("ital") for w in l["ws"]) or re.search(r"\d", t))
            # titulo da obra/credito em letra pequena logo acima de "Disponivel em..." tambem e fonte
            prox = partes_[i_parte + 1] if i_parte + 1 < len(partes_) else None
            titulo_fonte = (prox is not None and prox[0] == "linha" and abs(prox[1]["size"] - l["size"]) < 0.6
                            and RE_FONTE.search(txt_puro(prox[1])) and 0 <= prox[1]["top"] - l["bottom"] < 0.8 * CORPO
                            and not (prev is not None and prev.get("_fonte")))
            if RE_FONTE.search(t) or ref or titulo_fonte or (prev is not None and prev.get("_fonte")):
                flush(); l["_fonte"] = True
                nova_f = re.match(r"(?i)\W*(dispon[ií]vel em|disponible en|available|fonte:|fuente:|source:|foto:)", md)
                # continuacao: vai para a fonte cuja ultima linha esta logo acima desta (layout em colunas intercala linhas)
                alvo_f = None
                if not nova_f:
                    for k_, lf in ult_linha_fonte.items():
                        if lf.get("pg") == l.get("pg") and 0 <= l["top"] - lf["bottom"] < 0.8 * CORPO and min(lf["x1"], l["x1"]) - max(lf["x0"], l["x0"]) > -5:
                            alvo_f = k_
                    if alvo_f is None and fontes and prev is not None and prev.get("_fonte"): alvo_f = len(fontes) - 1
                if alvo_f is not None:
                    ult = fontes[alvo_f].split(" ")[-1]
                    prim = (md.split() or [""])[0]
                    cont_url = ("http" in ult or "www" in ult) and re.search(r"[_\-/%]$", ult) and re.search(r"[/._%=?&-]", prim) \
                               and not re.match(r"(?i)\W*(acesso|accessed|acceso|consultado|dispon)", prim)
                    novo_credito = md.startswith("**") and not re.search(r"[-/]$", ult)     # outro credito (autor) em negrito
                    fontes[alvo_f] += ("" if cont_url else "  \n" if novo_credito else " ") + md
                else:
                    fontes.append(md); alvo_f = len(fontes) - 1
                    if alt_atual is None: enun.append("{{fonte:%d}}" % len(fontes))   # a fonte fica no lugar onde aparece
                ult_linha_fonte[alvo_f] = l
                prev = l; continue
        if l.get("legenda_de") and alt_atual is None:      # legenda de figura: paragrafo proprio logo depois da figura
            if l["legenda_de"] in adiadas: figs_inicio.append(md); continue      # vai junto com a figura adiada
            flush(); destino().append(md); prev = l; continue
        # continua paragrafo ou abre outro
        if prev is None or par == "":
            par = md
            e_, d_ = it["borda"]; ant_curta = (l["x1"] - l["x0"]) < 0.8 * max(1, d_ - e_)
        else:
            gap = l["top"] - prev["bottom"]
            if ignora_gap:      # a figura adiada estava entre as duas linhas: o espaco dela nao conta
                gap = min(gap, 0); ignora_gap = False
            esq, dir_ = it["borda"]
            larg = max(1, dir_ - esq)
            # linha "curta" = a linha acabou antes da hora: a 1a palavra da linha seguinte caberia no espaco que sobrou
            # (o limite da direita e a borda do texto ou uma figura ao lado, quando o texto contorna a figura)
            lim = min(dir_, prev.get("lim_dir", 1e9) - 4)
            w1 = l["ws"][0]; larg_w1 = w1["x1"] - w1["x0"]
            prev_curta = (lim - prev["x1"]) > larg_w1 + 0.3 * prev["size"] and (lim - prev["x1"]) > 6
            verso = prev.get("irregular") and l.get("irregular") and mesma_col_(prev, l) and \
                    prev["x1"] < min(it.get("lim_col", dir_), prev.get("lim_dir", 1e9) - 4) - 12
            if verso: prev_curta = True
            atual_curta = (l["x1"] - l["x0"]) < 0.8 * larg
            mesma_col = abs(prev["col"][0] - l["col"][0]) < 1 and prev.get("pg") == l.get("pg")
            recuo = l["x0"] - esq > 6 and (not mesma_col or prev["x0"] - esq < 3)
            centrada = lambda z: z["x0"] - esq > 15 and dir_ - z["x1"] > 15 and abs((z["x0"] - esq) - (dir_ - z["x1"])) < 20
            # (bloco de texto ao lado de uma figura -- mesma esquerda da linha de cima -- nao e assinatura)
            bloco_lat = mesma_col_(prev, l) and abs(l["x0"] - prev["x0"]) < 2 and not centrada(prev)
            a_direita = l["x0"] - esq > 0.3 * larg and abs(l["x1"] - dir_) < 8 and not centrada(l) and not bloco_lat   # assinatura/autor
            fim_frase = re.search(r"[.:!?”\"»)]$", txt_puro(prev))
            topico = re.match(r"^\s*(•|–|—|-|▪|●|○)\s", txt_puro(l)) is not None
            # travessao no comeco da linha no meio de uma frase ("... em quase sua totalidade negros / — para enfrentar
            # ..."): linha de cima chega a margem e nao termina frase -> e continuacao, nao item de lista nem fala
            if topico and re.match(r"^\s*(–|—|-)\s", txt_puro(l)) and not fim_frase and not prev_curta \
                    and not re.search(r"[;,]$", txt_puro(prev)) and not prev.get("_topico"):
                topico = False
            # nome de personagem em maiusculas numa linha propria (dialogo de teatro) sempre comeca linha nova
            caixa_alta = len(l["ws"]) <= 3 and re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ.\s]{3,}", txt_puro(l).strip()) is not None and fim_frase_prev_ok(prev)
            l["_topico"] = topico      # so marcador/travessao (nome em maiusculas nao conta como item da lista)
            topico = topico or caixa_alta
            prev_topico = prev.get("_topico", re.match(r"^\s*(•|–|—|-|▪|●|○)\s", txt_puro(prev)) is not None)
            x_txt_topico = prev["ws"][1]["x0"] if prev_topico and len(prev["ws"]) > 1 else None
            fim_lista = prev_topico and not topico and (x_txt_topico is None or abs(l["x0"] - x_txt_topico) > 3)   # texto fora do recuo da lista
            gap_ref = max(GAP_L, GAP_REG.get((l.get("pg"), l.get("reg")), 0))
            novo_par = gap > gap_ref + 0.18 * CORPO or (recuo and (not prev_curta or fim_frase or prev_topico)) \
                       or (prev_curta and fim_frase and (not atual_curta or not ant_curta) and not verso) \
                       or (centrada(prev) != centrada(l)) or a_direita or fim_lista    # linha centralizada/assinatura: paragrafo proprio
            # item com recuo pendente ("I - A brutal diferenca ..." / "     etnicas no continente ..."): a linha que alinha
            # com o texto do item (ou com a linha anterior, no mesmo recuo) continua o item, a nao ser que haja espaco grande
            # ou o item anterior tenha terminado a frase numa linha curta
            alinhada_item = x_item is not None and abs(l["x0"] - x_item) < 2.5 and mesma_col
            mesmo_recuo = mesma_col and abs(l["x0"] - prev["x0"]) < 1.5 and l["x0"] - esq > 3 and alinhada_item
            if (alinhada_item or mesmo_recuo) and not RE_ITEM.match(txt_puro(l)) and not topico:
                novo_par = gap > gap_ref + 0.18 * CORPO or (prev_curta and fim_frase)
            if os.environ.get("DEBUGP") and re.search(os.environ["DEBUGP"], txt_puro(l)):
                print("DBGP", txt_puro(l)[:40], dict(gap=round(gap, 1), esq=esq, dir=dir_, prev_curta=prev_curta, atual_curta=atual_curta, recuo=recuo, fim=bool(fim_frase), topico=topico, prev_topico=prev_topico, fim_lista=fim_lista, novo=novo_par, x0=l["x0"]))
            if alt_atual is not None and pos_alt is None:    # dentro de uma alternativa as linhas sao uma frase continua
                novo_par = gap > 1.2 * CORPO; prev_curta = topico
                if novo_par and eh_questao and alt_atual["letra"] == ULT_LETRA and (alt_atual["md"] or par.strip()):
                    # paragrafo novo depois da ultima alternativa: nao e mais alternativa ("Note e adote:", dados)
                    flush(); pos_alt = []
            ant_curta = prev_curta and not novo_par
            if novo_par:
                flush(); par = md; ant_curta = atual_curta
            elif par.endswith("-") and md[:1].islower():
                par, duv = junta_hifen(par, md)
                if duv: alertas.append("palavra dividida no fim da linha com hífen incerto — conferir")
            elif prev_curta or topico:
                par = par.rstrip() + "  \n" + md       # quebra de linha (versos, titulos, itens de lista)
            else:
                par = par.rstrip() + " " + md
            par = re.sub(r"(?<!\*)\*\* \*\*(?!\*)", " ", par)     # negrito que continua na linha seguinte: um trecho so
        # recuo pendente de item: x onde comeca o texto depois do marcador ("I -", "II.", "1)", "•")
        mi_ = RE_ITEM.match(txt_puro(l))
        if mi_ and len(l["ws"]) > len(mi_.group(0).split()):
            x_item = l["ws"][len(mi_.group(0).split())]["x0"]
        elif prev is not None and l["x0"] - it["borda"][0] < 3:
            x_item = None
        prev = l
    flush()
    # alternativa marcada no caderno: so se UMA letra e bem mais escura que todas as outras (letras sempre em
    # circulo, como no Bernoulli, nao contam)
    rz = sorted(marcada, reverse=True)
    marc_ = rz[0][1] if len(rz) >= 4 and rz[0][0] > 0.45 and rz[1][0] < 0.6 * rz[0][0] else None
    # figuras das alternativas: cada uma vai para a alternativa cujo marcador (a), b)...) esta logo acima/a esquerda dela
    # (grade de figuras le em ordem diferente da ordem das letras)
    for k_, pg_f, bb_f, alt_cor in figs_alt:
        # marcador na mesma faixa de altura da figura (ao lado dela, ou logo acima) e a esquerda: o mais perto na horizontal
        cands_ = [a_ for a_ in alts if a_.get("pos") and a_["pos"][0] == pg_f and a_["pos"][1] <= bb_f[0] + 15
                  and bb_f[1] - 40 <= a_["pos"][2] <= bb_f[3]]
        # figura ao lado de VARIAS alternativas de texto (grafico a direita da lista a)...e)): e figura da questao, nao de
        # uma alternativa -> vai para antes do enunciado
        cobre_ = [a_ for a_ in cands_ if bb_f[1] + 2 <= a_["pos"][2] <= bb_f[3] - 2 and a_["pos"][1] < bb_f[0] - 5
                  and any(re.sub(r"\{\{img:\d+\}\}", "", m_).strip() for m_ in a_["md"])]
        if len(cobre_) >= 2:
            enun.insert(0, "{{img:%d}}" % k_); continue
        # marcador AO LADO da figura (dentro da altura dela) vence o que esta acima (figura alta que comeca acima da
        # propria letra, ex.: circuito da alternativa E comecando na altura da D)
        alvo_ = min(cands_, key=lambda a_: (round((bb_f[0] - a_["pos"][1]) / 10), not (bb_f[1] <= a_["pos"][2] <= bb_f[3]),
                                            abs(a_["pos"][2] - bb_f[1]))) if cands_ else alt_cor
        alvo_["md"].append("{{img:%d}}" % k_)
    # fileira de figuras com a letra embaixo de cada uma ("(A)" sob a foto A): a figura e a alternativa
    for a_ in alts:
        if a_["md"] or not a_.get("pos"): continue
        pg_a, xa_, ya_ = a_["pos"]
        for im_ in imagens:
            bb_ = im_["bbox"]; ph_ = "{{img:%d}}" % im_["id"]
            if im_["pagina"] == pg_a and bb_[3] - 4 <= ya_ <= bb_[3] + 20 and bb_[0] - 5 <= xa_ + 5 <= bb_[2] + 5 and ph_ in enun:
                enun.remove(ph_); a_["md"].append(ph_); break
    # o que vem depois das alternativas ("Note e adote", dados) fica num campo proprio, mostrado depois delas (como no original)
    if figs_inicio: enun = figs_inicio + enun
    res = {"apos_alternativas": "\n\n".join(pos_alt or []), "marcada": marc_, "enunciado": "\n\n".join(enun), "fontes": fontes, "imagens": imagens, "alertas": alertas}
    if eh_questao:
        # a letra de cada alternativa e explicita; em layout de grade (A D / B E / C) a ordem de leitura muda, entao ordena pela letra
        res["alternativas"] = sorted(({"letra": a["letra"], "texto": "\n\n".join(a["md"])} for a in alts), key=lambda a: a["letra"])
    return res

# ------------------------------------------------------------------ gabarito
def le_gabarito(ids=None):
    gab = {}
    ids = (P.get("gabarito_ids") or "").split() if ids is None else ids
    for gid in ids:
        g = CAT.get(gid)
        if not g: continue
        t = subprocess.run(["pdftotext", "-layout", os.path.join(RAIZ, g["caminho"]), "-"], capture_output=True).stdout.decode("utf-8", "replace")
        # tabela horizontal: "Questao 1 2 3 ..." e, logo abaixo, "Gabarito B A E ..." (mesma quantidade)
        lin_ = [x for x in t.splitlines() if x.strip()]
        for a_, b_ in zip(lin_, lin_[1:]):
            rot_ = re.match(r"(?i)^\s*quest", a_) and re.match(r"(?i)^\s*(gabarito|resposta)", b_)
            ta = re.sub(r"(?i)^\s*quest(ão|ao|ões|oes)\s*", "", a_).split()
            tb_ = re.sub(r"(?i)^\s*(gabarito|resposta)s?\s*", "", b_).split()
            if len(ta) >= (1 if rot_ else 5) and len(ta) == len(tb_) and all(x.isdigit() for x in ta) and all(re.fullmatch(r"[A-E]|(?i:anulad[ao])|\*", x) for x in tb_):
                for n_, g_ in zip(ta, tb_):
                    if g_ != "*": gab.setdefault(int(n_), g_)
        # resolucao comentada: "QUESTAO 12 ... C) CORRETA"
        for mq in re.finditer(r"(?s)QUEST[ÃA]O\s+0*(\d{1,3})\b(.*?)(?=QUEST[ÃA]O\s+\d|\Z)", t):
            mc = re.search(r"\b([A-E])\)\s*CORRETA\b", mq.group(2))
            if mc: gab.setdefault(int(mq.group(1)), mc.group(1))
        for linha in t.splitlines():
            toks = re.findall(r"(?<![\w,])\d{1,3}(?![\w,])|Anulad[ao]|ANULAD[AO]|(?<![A-Za-zÀ-ÿ])[A-E](?![A-Za-zÀ-ÿ])", linha)
            n = None; letras = []
            def fecha():
                if n is None or not letras: return
                if len(letras) == 1: gab.setdefault(n, letras[0])
                elif len(letras) == 2: gab.setdefault((n, "inglês"), letras[0]); gab.setdefault((n, "espanhol"), letras[1])
            for tk in toks:
                if tk.isdigit(): fecha(); n = int(tk); letras = []
                else: letras.append(tk)
            fecha()
        # cartao de respostas desenhado: "91 - [A][B][#][D][E]" (a caixa cheia e a resposta; a letra nem e texto)
        try:
            with pdfplumber.open(os.path.join(RAIZ, g["caminho"])) as pdf_g:
                for pg_g in pdf_g.pages[:4]:
                    caixas_g = [r for r in pg_g.rects if 7 <= r["width"] <= 22 and 7 <= r["height"] <= 22]
                    if len(caixas_g) < 20: continue
                    for w in pg_g.extract_words():
                        if not re.fullmatch(r"\d{1,3}", w["text"]): continue
                        lin_c = sorted([r for r in caixas_g if abs(r["top"] - w["top"]) < 6 and w["x1"] < r["x0"] < w["x1"] + 130], key=lambda r: r["x0"])
                        xs = []
                        for r in lin_c:
                            if not xs or r["x0"] - xs[-1] > 3: xs.append(r["x0"])
                        if len(xs) not in (4, 5): continue
                        xs = xs[:len(xs)]
                        escuro = lambda r: r.get("fill") and all(v <= 0.3 for v in (r.get("non_stroking_color") or (1,))[:3]) if len(r.get("non_stroking_color") or ()) >= 3 \
                            else r.get("fill") and (r.get("non_stroking_color") or (0,))[-1] >= 0.8
                        cheias = {min(range(len(xs)), key=lambda k: abs(xs[k] - r["x0"])) for r in lin_c if escuro(r)}
                        if len(cheias) == 1: gab[int(w["text"])] = "ABCDE"[cheias.pop()]    # cartao vale mais que texto solto
        except Exception:
            pass
    return gab, ids
GAB, GAB_IDS = le_gabarito()
# gabarito pareado que nao cobre as questoes (arquivo trocado, ex.: "Gabarito Primeiro dia" com o 2o dia): procura entre
# os gabaritos da mesma pasta o que cobre os numeros desta prova
_nums_q = {q["numero"] for q in questoes}
_cobre = lambda g: len(_nums_q & {k if isinstance(k, int) else k[0] for k in g}) / max(1, len(_nums_q))
if _nums_q and _cobre(GAB) < 0.5:
    _pasta = os.path.dirname(P["caminho"])
    _irmaos = [d["id"] for d in CAT.values() if os.path.dirname(d["caminho"]) == _pasta and d.get("papel") == "gabarito"
               and d["id"] not in GAB_IDS and os.path.exists(os.path.join(RAIZ, d["caminho"]))]
    _melhor = max(((_cobre(g_), gid_, g_) for gid_ in _irmaos for g_ in [le_gabarito([gid_])[0]]), default=None, key=lambda x: x[0])
    if _melhor and _melhor[0] >= 0.8:
        print(f"gabarito pareado não cobre as questões; usando {_melhor[1]} da mesma pasta (cobre {_melhor[0]:.0%})")
        GAB, GAB_IDS = _melhor[2], [_melhor[1]]
        GAB_TROCADO = True

# ------------------------------------------------------------------ alternativas desenhadas (sem texto no PDF)
def alt_sobre_imagem(q, r):
    """ha N_ALT letras de alternativa, uma embaixo da outra, na altura de uma mesma imagem da questao (a esquerda dela)"""
    ids_alt = [int(m_.group(1)) for a_ in r["alternativas"] for m_ in [re.fullmatch(r"\s*\{\{img:(\d+)\}\}\s*", a_["texto"])] if m_]
    ims_alt = [i_ for i_ in r["imagens"] if i_["id"] in ids_alt]
    cands_ = list(r["imagens"])
    if len(ims_alt) >= 2 and len({i_["pagina"] for i_ in ims_alt}) == 1:
        bbs = [i_["bbox"] for i_ in ims_alt]
        cands_.append({"pagina": ims_alt[0]["pagina"], "bbox": [min(b_[0] for b_ in bbs), min(b_[1] for b_ in bbs), max(b_[2] for b_ in bbs), max(b_[3] for b_ in bbs)]})
    for im in cands_:
        bb = im["bbox"]; pg = paginas[im["pagina"] - 1]
        ls = {w["text"].strip("()").upper() for w in pg["ws"] if re.fullmatch(r"\(?[a-eA-E]\)", w["text"])
              and bb[1] - 2 <= (w["top"] + w["bottom"]) / 2 <= bb[3] + 2 and w["x1"] <= bb[2]}
        if ls >= set("ABCDE"[:N_ALT]): return True
    return False
def alternativas_em_tabela(q, r, multi=False):
    """Alternativas dentro de uma tabela (cada linha da tabela = uma alternativa, com a letra ao lado ou na 1a coluna):
    cada alternativa vira uma tabelinha com o cabecalho + a sua linha, em texto (nada de foto de tabela)."""
    cands_im = list(reversed(r["imagens"]))
    # alternativas ja recortadas uma por imagem (uma linha da tabela cada): a tabela inteira e a uniao delas
    ids_alt = [int(m_.group(1)) for a_ in r["alternativas"] for m_ in [re.fullmatch(r"\s*\{\{img:(\d+)\}\}\s*", a_["texto"])] if m_]
    ims_alt = [i_ for i_ in r["imagens"] if i_["id"] in ids_alt]
    if len(ims_alt) >= 2 and len({i_["pagina"] for i_ in ims_alt}) == 1:
        bbs = [i_["bbox"] for i_ in ims_alt]
        cands_im.insert(0, {"id": ims_alt[0]["id"], "pagina": ims_alt[0]["pagina"], "uniao": [i_["id"] for i_ in ims_alt],
                            "bbox": [min(b_[0] for b_ in bbs), min(b_[1] for b_ in bbs), max(b_[2] for b_ in bbs), max(b_[3] for b_ in bbs)]})
    for im in cands_im:
        pg = paginas[im["pagina"] - 1]; page = pg["page"]; bb = im["bbox"]
        # a area vai ate as bordas do texto da questao na pagina (a letra e colunas podem ter ficado fora do recorte)
        cx_q = [c_ for c_ in (q.get("caixas") or {}).get(im["pagina"], []) if min(c_[3], bb[3]) - max(c_[1], bb[1]) > 0]
        ax0 = min([bb[0] - 45] + [c_[0] - 2 for c_ in cx_q]); ax1 = max([bb[2] + 2] + [c_[2] + 2 for c_ in cx_q])
        area = (max(0, ax0), max(0, bb[1] - 2), min(page.width, ax1), min(page.height, bb[3] + 2))
        try:
            tabs = page.crop(area).find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines"})
        except Exception:
            continue
        tabs2 = []
        for tb in tabs:
            # tabela sem o fio da direita (ou da esquerda): o texto das linhas continua do lado de fora da grade ->
            # a grade ganha um fio no fim do texto
            fora_d = [w for w in pg["ws"] if w["x0"] > tb.bbox[2] + 1 and w["x1"] <= area[2] + 1 and tb.bbox[1] <= (w["top"] + w["bottom"]) / 2 <= tb.bbox[3]]
            if fora_d:
                try:
                    tt_ = page.crop(area).find_tables({"vertical_strategy": "lines", "horizontal_strategy": "lines",
                                                       "explicit_vertical_lines": [max(w["x1"] for w in fora_d) + 2]})
                    tt_ = [t_ for t_ in tt_ if t_.bbox[0] <= tb.bbox[0] + 1 and t_.bbox[1] <= tb.bbox[1] + 1]
                    if tt_: tabs2.append(tt_[0]); continue
                except Exception:
                    pass
            tabs2.append(tb)
        for tb in tabs2:
            linhas_t = tb.rows
            if len(linhas_t) < N_ALT: continue
            def txt_cel(cb):
                if cb is None: return ""
                wc = sorted([w for w in pg["ws"] if cb[0] - 0.5 <= (w["x0"] + w["x1"]) / 2 <= cb[2] + 0.5 and cb[1] - 0.5 <= (w["top"] + w["bottom"]) / 2 <= cb[3] + 0.5],
                            key=lambda w: (round(w["top"] / 3), w["x0"]))
                grupos_c = []
                for w in wc:
                    if grupos_c and abs(grupos_c[-1][0]["top"] - w["top"]) < 0.5 * w["size"]: grupos_c[-1].append(w)
                    else: grupos_c.append([w])
                return re.sub(r"(?<!\*)\*\* \*\*(?!\*)", " ", " ".join(md_linha({"ws": sorted(g_, key=lambda w: w["x0"])}) for g_ in grupos_c))
            dados = [[txt_cel(cb) for cb in row.cells] for row in linhas_t]
            # colunas vazias em todas as linhas (celulas mescladas) saem
            ncol = max(len(rw) for rw in dados)
            dados = [rw + [""] * (ncol - len(rw)) for rw in dados]
            cheias = [j_ for j_ in range(ncol) if any(rw[j_].strip() for rw in dados)]
            dados = [[rw[j_] for j_ in cheias] for rw in dados]
            x0t = tb.bbox[0]
            letras_w = [w for w in pg["ws"] if re.fullmatch(r"\(?[a-eA-E]\)", w["text"]) and w["x1"] <= x0t + 25 and w["x0"] >= x0t - 45]
            mapa = {}
            for k_, row in enumerate(linhas_t):
                y0_, y1_ = row.bbox[1], row.bbox[3]
                ls = [w for w in letras_w if y0_ <= (w["top"] + w["bottom"]) / 2 <= y1_]
                if len(ls) == 1: mapa[k_] = ls[0]["text"].strip("()").upper()
            ordem = [mapa[k_] for k_ in sorted(mapa)]
            if ordem != list("ABCDE"[:N_ALT]): continue
            prim = min(mapa); cab = dados[:prim]; cab_de_cima = False
            if not cab:
                # cabecalho logo acima da grade, sem fio ("X   Y   Z"): cada palavra cai na coluna que a contem
                cels_ = [cb for cb in linhas_t[prim].cells if cb is not None]
                ws_cab = [w for w in pg["ws"] if 0 <= tb.bbox[1] - w["bottom"] < 8 and tb.bbox[0] - 1 <= w["x0"] and w["x1"] <= tb.bbox[2] + 1]
                if ws_cab:
                    lin_c = []
                    for cb in cels_:
                        ws_c = [w for w in ws_cab if cb[0] <= (w["x0"] + w["x1"]) / 2 <= cb[2]]
                        lin_c.append(" ".join(md_linha({"ws": [w]}) for w in sorted(ws_c, key=lambda w: w["x0"])))
                    if sum(1 for w in ws_cab if any(cb[0] <= (w["x0"] + w["x1"]) / 2 <= cb[2] for cb in cels_)) == len(ws_cab):
                        cab = [lin_c]; cab_de_cima = True
            # celulas de cada linha sem as vazias (celula mesclada) e sem a letra; cabecalho e linhas tem de casar
            limpa_l = lambda rw: [" ".join(c_.split()) for c_ in rw if c_.strip() and not re.fullmatch(r"\**\(?[a-eA-E]\)\**", c_.strip())]
            h_ = limpa_l(cab[-1]) if cab else []
            rows_a = {k_: limpa_l(dados[k_]) for k_ in mapa}
            if any(not v for v in rows_a.values()) or len({len(v) for v in rows_a.values()}) != 1: continue
            if h_ and len(h_) != len(next(iter(rows_a.values()))): continue
            if multi and len(next(iter(rows_a.values()))) < 2: continue    # (alternativas ja lidas: so tabela de verdade, com 2+ colunas)
            def md_(rw):
                out = []
                if h_: out += ["| " + " | ".join(h_) + " |", "|" + "---|" * len(h_)]
                else: out += ["| " + " | ".join([" "] * len(rw)) + " |", "|" + "---|" * len(rw)]
                out.append("| " + " | ".join(rw) + " |")
                return "\n".join(out)
            alts = [{"letra": mapa[k_], "texto": md_(rows_a[k_])} for k_ in sorted(mapa)]
            r["alternativas"] = alts
            # imagem(ns) da tabela saem; pedaco do cabecalho que tinha sobrado como texto solto COLADO a imagem ("**X**") sai
            pal_cab = {re.sub(r"\W", "", c_) for c_ in " ".join(h_).split()}
            ids_ = im.get("uniao") or [im["id"]]
            phs = {"{{img:%d}}" % i_ for i_ in ids_}
            pars = r["enunciado"].split("\n\n")
            eh_cab_p = lambda p_: p_.strip() and len(p_) <= 40 and {re.sub(r"\W", "", x_) for x_ in p_.split()} <= pal_cab
            tirar_p = set()
            for i_p, p_ in enumerate(pars):
                if p_.strip() in phs:
                    tirar_p.add(i_p)
                    for d_ in (1, -1):
                        j_ = i_p + d_
                        while 0 <= j_ < len(pars) and (eh_cab_p(pars[j_]) or pars[j_].strip() in phs):
                            tirar_p.add(j_); j_ += d_
            r["enunciado"] = "\n\n".join(p_ for i_p, p_ in enumerate(pars) if i_p not in tirar_p)
            r["imagens"] = [i_ for i_ in r["imagens"] if i_["id"] not in ids_]
            r["alertas"] = [a_ for a_ in r["alertas"] if not any(a_.startswith(f"imagem {i_} ") for i_ in ids_)
                            and "texto desenhado no PDF" not in a_]
            r["alertas"].append("alternativas em tabela transcritas como texto (cabeçalho + linha de cada alternativa) — conferir")
            return True
    return False
def separa_alternativas_em_imagem(q, r):
    """Quando as alternativas estao no PDF como desenho (sem texto), elas caem dentro da ultima figura.
    O OCR so e usado para ACHAR os marcadores a) b) c) d) e); o conteudo continua sendo a imagem recortada."""
    im = r["imagens"][-1]; arq = os.path.join(OUT, im["arquivo"])
    try:
        tsv = subprocess.run(["tesseract", arq, "-", "--psm", "6", "tsv"], capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return
    img = cv2.imread(arq); H, W = img.shape[:2]
    letras_q = "abcde"[:N_ALT]
    marc = {}
    for linha in tsv.splitlines()[1:]:
        c = linha.split("\t")
        if len(c) < 12: continue
        t = c[11].strip()
        m = re.fullmatch(r"\(?([a-eA-E])\)", t)
        if m:
            marc.setdefault(m.group(1).lower(), (int(c[6]), int(c[7]), int(c[8]), int(c[9])))
    if sorted(marc) != list(letras_q):
        # a letra fica numa celula propria da tabela ("a)" | desenho): acha as celulas pela grade e le cada letra sozinha
        cel_ = alternativas_em_celulas(img, letras_q)
        if cel_ is None: return
        marc, caixas = cel_
        return corta_alternativas(q, r, im, arq, img, letras_q, marc, caixas, grade=True)
    # colunas: marcadores alinhados na mesma vertical (layout em grade, ex.: a b c | d e)
    cols = []
    for k in letras_q:
        x = marc[k][0]
        for col in cols:
            if abs(marc[col[0]][0] - x) < 0.08 * W: col.append(k); break
        else: cols.append([k])
    cols.sort(key=lambda col: marc[col[0]][0])
    # ordem de leitura: coluna por coluna, de cima para baixo, tem de dar a, b, c, d, e
    leitura = [k for col in cols for k in sorted(col, key=lambda k: marc[k][1])]
    if leitura != list(letras_q): return
    caixas = {}
    for ci, col in enumerate(cols):
        x_fim = (min(marc[k][0] for k in cols[ci + 1]) - 6) if ci + 1 < len(cols) else W
        col_o = sorted(col, key=lambda k: marc[k][1])
        for i_, k in enumerate(col_o):
            x0 = marc[k][0] + marc[k][2] + 4
            y0 = max(0, marc[k][1] - 8); y1 = (marc[col_o[i_ + 1]][1] - 8) if i_ + 1 < len(col_o) else H
            caixas[k] = (x0, y0, x_fim, y1)
    return corta_alternativas(q, r, im, arq, img, letras_q, marc, caixas)
def alternativas_em_celulas(img, letras_q):
    """grade desenhada na imagem: celula estreita com a letra + celula larga com o conteudo, lado a lado.
    Devolve (marc, caixas) ou None. A letra de cada celula estreita e lida sozinha pelo OCR (tem de dar a..e)."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    H, W = g.shape
    bw = (g < 215).astype(np.uint8)      # (fio da grade pode ser cinza claro)
    hz = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((1, max(20, W // 8)), np.uint8))
    vt = cv2.morphologyEx(bw, cv2.MORPH_OPEN, np.ones((max(20, H // 12), 1), np.uint8))
    grade = cv2.dilate(hz | vt, np.ones((3, 3), np.uint8))
    n_, lab_, st_, _ = cv2.connectedComponentsWithStats(1 - grade, 4)
    cels = [tuple(st_[k][:4]) for k in range(1, n_) if st_[k][2] > 8 and st_[k][3] > 0.05 * H
            and st_[k][0] > 0 and st_[k][1] > 0 and st_[k][0] + st_[k][2] < W and st_[k][1] + st_[k][3] < H]
    pares = []
    for c in cels:
        x, y, w, h = c
        viz = [d for d in cels if d is not c and abs(d[1] - y) < 0.15 * h and abs(d[3] - h) < 0.15 * h and 0 <= d[0] - (x + w) < 12 and d[2] > 2 * w]
        if len(viz) == 1: pares.append((c, viz[0]))
    if len(pares) != len(letras_q): return None
    marc = {}; caixas = {}
    for c, d in pares:
        x, y, w, h = c
        cel_img = g[y:y + h, x:x + w]
        cel_img = cv2.resize(cel_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        tmp_ = os.path.join(TMP, f"_cel_{PID}_{os.getpid()}.png"); cv2.imwrite(tmp_, cel_img)
        try:
            t = subprocess.run(["tesseract", tmp_, "-", "--psm", "7"], capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception:
            return None
        m = re.fullmatch(r"\(?([a-eA-E])\)?", t.replace(" ", ""))
        if not m or m.group(1).lower() in marc: return None
        k = m.group(1).lower()
        marc[k] = (x, y, w, h); caixas[k] = (d[0], d[1], d[0] + d[2], d[1] + d[3])
    if sorted(marc) != list(letras_q): return None
    return marc, caixas
def corta_alternativas(q, r, im, arq, img, letras_q, marc, caixas, grade=False):
    H, W = img.shape[:2]
    novas = []
    for i, k in enumerate(letras_q):
        x0, y0, x1, y1 = caixas[k]
        nome = f"img/{q['cod']}_alt{k}.png"
        cv2.imwrite(os.path.join(OUT, nome), img[y0:y1, x0:x1])
        novas.append({"id": len(r["imagens"]) + i + 1, "arquivo": nome, "pagina": im["pagina"], "bbox": im["bbox"], "recorte_de": im["id"]})
    y_a = max(0, min(marc[k][1] for k in letras_q) - 8)
    ph = f"{{{{img:{im['id']}}}}}"
    if grade: y_a = max(0, min(caixas[k][1] for k in letras_q) - 8)
    else:
        # o corte sobe ate uma faixa branca (o radical/fracao da alternativa a) e mais alto que a letra "a)")
        g_ = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        y_b = y_a
        while y_b > 0 and y_a - y_b < 60 and (g_[y_b] < 200).any(): y_b -= 1
        if y_b > 0 and (g_[y_b] >= 200).all(): y_a = y_b
    if y_a > (0.1 * H if grade else 20):   # sobra algo antes do a): mantem a parte de cima como figura do enunciado
        cv2.imwrite(arq, img[:y_a, :])
    else:
        r["enunciado"] = r["enunciado"].replace(ph, "").strip(); r["imagens"].remove(im)
    r["imagens"] += novas
    r["alternativas"] = [{"letra": k.upper(), "texto": f"{{{{img:{n['id']}}}}}"} for k, n in zip(letras_q, novas)]
    # alternativa baixa (altura de uma linha) = texto desenhado -> precisa transcrever; alta = grafico/esquema (fica imagem)
    baixas = [k.upper() for k in letras_q if (caixas[k][3] - caixas[k][1]) / (DPI_FIG / 72) < 2.2 * CORPO]
    if baixas:
        r["alertas"].append("alternativas estão desenhadas no PDF (sem texto): recortadas como imagem, uma por alternativa — conferir")
    else:
        r["alertas"].append("alternativas são figuras (gráficos/esquemas) numa imagem só: recortadas uma por alternativa — conferir o recorte")

# ------------------------------------------------------------------ transcricoes por visao / correcoes revisadas
# Quando o PDF nao tem texto num trecho (letras desenhadas como curvas) ou o layout e complexo demais,
# o Claude le a imagem da pagina e grava o texto em _banco/transcricoes/<id_prova>.json. O extrator aplica aqui.
TRANS_P = os.path.join(B, "transcricoes", PID + ".json")
TRANS = json.load(open(TRANS_P, encoding="utf-8")) if os.path.exists(TRANS_P) else {}
PENDENTES_VISAO = []
def aplica_transcricao(q, r):
    t = TRANS.get(q["cod"])
    alts_img = [a for a in r["alternativas"] if re.fullmatch(r"\s*\{\{img:\d+\}\}\s*", a["texto"]) and "_alt" in json.dumps(r["imagens"])]
    # alternativa que e so uma imagem da altura de uma linha de texto = texto desenhado com curvas (sem camada de texto)
    ims = {i["id"]: i for i in r["imagens"]}
    alt_linha = []
    for a in r["alternativas"]:
        m_ = re.fullmatch(r"\s*\{\{img:(\d+)\}\}\s*", a["texto"])
        if m_ and int(m_.group(1)) in ims:
            bb = ims[int(m_.group(1))]["bbox"]
            if bb[3] - bb[1] < 2.2 * CORPO: alt_linha.append(a["letra"])
    t = t or {}
    if alt_linha and "alternativas" not in t:
        r["alertas"].append("alternativas " + ", ".join(alt_linha) + " são texto desenhado no PDF (sem camada de texto): recortadas como imagem — precisam ser transcritas")
    falta_alt = "alternativas" not in t and (not r["alternativas"] or alt_linha or any("desenhadas no PDF" in a for a in r["alertas"]))
    falta_enun = "enunciado" not in t and any("trecho desenhado" in a for a in r["alertas"])
    if falta_alt or falta_enun:
        PENDENTES_VISAO.append(q["cod"])
        r["alertas"].append("PENDENTE: o texto deste trecho precisa ser transcrito lendo a imagem da página")
    if not t: return
    if "enunciado" in t:
        r["enunciado"] = t["enunciado"]
    if "fontes" in t:
        r["fontes"] = t["fontes"]
    if "apos_alternativas" in t:
        r["apos_alternativas"] = t["apos_alternativas"]
    if "alternativas" in t:
        r["alternativas"] = [{"letra": k, "texto": v} for k, v in sorted(t["alternativas"].items())]
    usados = set(re.findall(r"\{\{img:(\d+)\}\}", r["enunciado"] + json.dumps(r["alternativas"], ensure_ascii=False) + (r.get("apos_alternativas") or "")))
    r["imagens"] = [i for i in r["imagens"] if str(i["id"]) in usados]
    r["alertas"] = [a for a in r["alertas"] if "alternativas encontradas" not in a and not ("desenhadas no PDF" in a and "alternativas" in t)
                    and not ("trecho desenhado" in a and "enunciado" in t)]
    r["alertas"].append(t.get("nota", "texto transcrito lendo a imagem da página (o PDF não tem texto neste trecho) — conferir"))

# ------------------------------------------------------------------ saida
saida_q = []; saida_t = []
for tb in textos_base:
    r = monta(tb, tb["id"].split("-")[-1], False)
    aplica_branco(r)
    tb_out = {"id": tb["id"], "texto": r["enunciado"], "fontes": r["fontes"], "imagens": r["imagens"], "alertas": r["alertas"],
              "paginas": sorted(tb["caixas"].keys()), "caixas": {str(k): v for k, v in tb["caixas"].items()}, "faixa_questoes": tb.get("faixa")}
    saida_t.append(tb_out)
SUF = {"inglês": "-ING", "espanhol": "-ESP", None: ""}
# "Texto N" -> texto-base que contem esse texto (por idioma). Usado quando a questao cita um texto especifico.
RE_CITA = re.compile(r"(?i)\btext(?:o|os|s)?\s+(0*\d{1,2}(?:\s*(?:,|e|and|y)\s*0*\d{1,2})*)\b")
rotulo_base = {}   # (idioma, numero) -> [(pontos, id)]
for tb, tbo in zip(textos_base, saida_t):
    plano = tbo["texto"]
    for mm in re.finditer(r"(?i)(\*\*)?\btext(?:o|s)?\s+0*(\d{1,2})\b", plano):
        pontos = 2 if mm.group(1) else 1
        rotulo_base.setdefault((tb.get("idioma"), int(mm.group(2))), []).append((pontos, tb["id"]))
def bases_citadas(texto, idioma):
    ids = []
    for mm in RE_CITA.finditer(texto.replace("*", "")):
        for n in re.findall(r"\d{1,2}", mm.group(1)):
            cand = rotulo_base.get((idioma, int(n))) or ([] if idioma is None else rotulo_base.get((None, int(n)), []))
            if cand:
                melhor = max(cand, key=lambda c: c[0])[1]
                if melhor not in ids: ids.append(melhor)
    return ids
for q in questoes:
    q["cod"] = f"Q{q['numero']:03d}{SUF[q.get('idioma')]}"
    r = monta(q, q["cod"], True)
    if r["alternativas"] and r["imagens"] and alt_sobre_imagem(q, r):
        # as linhas das alternativas estao dentro/ao lado de uma grade (cada alternativa = uma linha da tabela)
        alternativas_em_tabela(q, r, multi=True)
    if not r["alternativas"] and r["imagens"]:
        if not alternativas_em_tabela(q, r):
            separa_alternativas_em_imagem(q, r)
    aplica_transcricao(q, r)
    aplica_branco(r)
    al = r["alertas"]
    if len(r["alternativas"]) != N_ALT: al.append(f"{len(r['alternativas'])} alternativas encontradas (esperado {N_ALT})")
    letras = "".join(a["letra"] for a in r["alternativas"])
    if letras and letras != "ABCDE"[:len(letras)]: al.append(f"letras fora de ordem: {letras}")
    if any(not a["texto"].strip() for a in r["alternativas"]): al.append("alternativa vazia")
    # conferencias extras
    txts_alt = [re.sub(r"\s+", " ", a["texto"]).strip() for a in r["alternativas"] if a["texto"].strip()]
    if len(set(txts_alt)) < len(txts_alt): al.append("há alternativas com texto idêntico — conferir")
    apos_ = r.get("apos_alternativas", "").strip()
    if apos_ and not re.match(r"(?i)\W*(note e adote|dados|adote|obs|observa[çc][ãa]o|considere|use|utilize|informa[çc]|constantes|tabela peri)", apos_):
        al.append("há texto depois das alternativas (“%s”): conferir se é desta questão" % re.sub(r"\s+", " ", apos_)[:50])
    pars_ = [p for p in r["enunciado"].split("\n\n") if p.strip()]
    for i_, p_ in enumerate(pars_):
        if p_.startswith("{{"): continue
        viz_img = any(re.fullmatch(r"\{\{img:\d+\}\}", pars_[j_].strip()) for j_ in (i_ - 1, i_ + 1) if 0 <= j_ < len(pars_))
        if viz_img and len(re.sub(r"<[^>]+>|\*|\\\(.*?\\\)", " ", p_).split()) <= 3 and not re.search(r"[.:?!]$", p_.strip()) \
                and not re.fullmatch(r"\**\s*(TEXTO|Texto|FIGURA|Figura|Imagem|IMAGEM|Tabela|TABELA|Gráfico|GRÁFICO)\s+[IVX\d]+\s*\**", p_.strip()):
            al.append(f"texto curto solto junto da imagem (“{p_[:40]}”): pode ser rótulo da figura — conferir")
    if re.search(r"[-�]", r["enunciado"] + json.dumps(r["alternativas"], ensure_ascii=False)): al.append("caractere estranho no texto")
    g = GAB.get((q["numero"], q["idioma"])) if q.get("idioma") else None
    g = g or GAB.get(q["numero"])
    if g and r.get("marcada") and g.upper() != r["marcada"] and not g.lower().startswith("anul"):
        al.append(f"gabarito do arquivo ({g}) diferente da alternativa marcada no caderno ({r['marcada']}) — conferir")
    if not g and r.get("marcada"):
        g = r["marcada"]      # caderno com a resposta marcada (circulo cheio na letra)
    if not g: al.append("sem gabarito")
    base = None
    if PERFIL == "ssa":
        for tb, tbo in zip(textos_base, saida_t):
            fx = tb.get("faixa")
            if fx and fx[0] <= q["numero"] <= fx[1] and tb.get("idioma") in (None, q.get("idioma")): base = tb["id"]
        if base is None: base = q.get("base_ref")
    # questao que cita um texto especifico ("Texto 7", "Textos 4 e 5"): o(s) texto(s) vao junto, para a questao
    # poder ser lida sozinha no banco. Vale para qualquer prova, mas so quando ha a citacao.
    citadas = bases_citadas(r["enunciado"] + " " + " ".join(a_["texto"] for a_ in r["alternativas"]), q.get("idioma"))
    bases_q = ([base] if base else []) + [c for c in citadas if c != base]
    if citadas and base and base not in citadas:
        # o texto-base "vizinho" nao e o citado: fica so o citado (ex.: questao que fala do Texto 2 logo depois do Texto 3)
        bases_q = citadas
    if not base and bases_q: base = bases_q[0]
    saida_q.append({
        "id": f"{PID}-{q['cod']}", "prova_id": PID, "idioma": q.get("idioma"), "vestibular": P["vestibular"], "ano": P["ano"], "edicao": P["edicao"],
        "fase_etapa": P["fase_etapa"], "dia": P["dia"], "caderno": P["caderno"], "numero": q["numero"], "area": q.get("area", ""),
        "texto_base_id": base, "textos_base_ids": bases_q, "enunciado": r["enunciado"], "fontes": r["fontes"], "alternativas": r["alternativas"],
        "apos_alternativas": r.get("apos_alternativas", ""),
        "imagens": r["imagens"], "gabarito": None if (g or "").lower().startswith("anul") else g,
        "anulada": bool(g and g.lower().startswith("anul")),
        "paginas": sorted(q["caixas"].keys()), "caixas": {str(k): v for k, v in q["caixas"].items()},
        "arquivo_origem": P["caminho"], "gabarito_origem": GAB_IDS, "alertas": al,
        "status_revisao": "revisar" if al else "automático ok"})

# conferencia de cobertura: toda linha de texto da prova tem de ter ido para algum lugar
primeira_pg = min((min(int(k) for k in q["caixas"]) for q in saida_q + saida_t if q["caixas"]), default=1)
ultima_pg = max((max(int(k) for k in q["caixas"]) for q in saida_q), default=NPAG)
perdidas = []
for pg in paginas:
    if not (primeira_pg <= pg["n"] <= ultima_pg): continue
    for l in pg["linhas"]:
        if l.get("fig") is None and not l.get("uso"):
            perdidas.append((pg["n"], l))
if os.environ.get("DEBUGTXT"):
    for pg in paginas:
        for l in pg["linhas"]:
            if re.search(os.environ["DEBUGTXT"], txt_puro(l)): print("DBG", pg["n"], txt_puro(l)[:60], l.get("uso"), l.get("fig"))
for pn, l in perdidas:
    # alerta na questao mais proxima na mesma pagina
    melhor = None
    for q in saida_q:
        for c in q["caixas"].get(pn, q["caixas"].get(str(pn), [])):
            d = min(abs(l["top"] - c[1]), abs(l["top"] - c[3]))
            if melhor is None or d < melhor[0]: melhor = (d, q)
    if melhor:
        melhor[1]["alertas"].append(f"linha da página {pn} não entrou em nenhuma questão: “{txt_puro(l)[:80]}”")
        melhor[1]["status_revisao"] = "revisar"
print(f"linhas de texto não aproveitadas (entre a 1ª e a última questão): {len(perdidas)}")

# textos-base que nenhuma questao usa ficam separados (instrucoes, capa...) para conferencia
vazios = {t["id"] for t in saida_t if not re.sub(r"\{\{fonte:\d+\}\}", "", t["texto"]).strip() and not t["imagens"]}
# texto-base que so tem a fonte/citacao (ex.: "Disponivel em..." depois das alternativas): a fonte volta para a questao anterior
for tb, t in zip(textos_base, saida_t):
    if t["id"] in vazios and t["fontes"] and tb.get("apos", -1) >= 0:
        cod = questoes[tb["apos"]]["cod"]
        for q in saida_q:
            if q["id"] == f"{PID}-{cod}":
                q["fontes"] += t["fontes"]; t["fontes"] = []; t["texto"] = re.sub(r"\{\{fonte:\d+\}\}", "", t["texto"]).strip()
for q in saida_q:
    q["textos_base_ids"] = [b_ for b_ in q["textos_base_ids"] if b_ not in vazios]
    q["texto_base_id"] = q["textos_base_ids"][0] if q["textos_base_ids"] else None
usados = {b_ for q in saida_q for b_ in q["textos_base_ids"]}
for t in saida_t:
    t["questoes"] = [q["id"] for q in saida_q if t["id"] in q["textos_base_ids"]]
nao_ligados = [t for t in saida_t if t["id"] not in usados]
saida_t = [t for t in saida_t if t["id"] in usados]

# posicao das fontes: cada fonte fica no lugar onde aparece no texto ({{fonte:N}}) e SEMPRE antes do comando da
# questao (o ultimo paragrafo do enunciado). Fonte que veio depois do comando/das alternativas sobe para antes dele.
RE_MARC_F = re.compile(r"^\{\{fonte:(\d+)\}\}$")
def posiciona_fontes(item, campo, eh_q):
    n_f = len(item["fontes"])
    eh_m = lambda p: RE_MARC_F.match(p.strip())
    eh_img = lambda p: re.fullmatch(r"\s*\{\{img:\d+\}\}\s*", p) is not None
    pars, vistos = [], set()
    for p in (x for x in item[campo].split("\n\n") if x.strip()):
        m = eh_m(p)
        if m:
            k = int(m.group(1))
            if not (1 <= k <= n_f) or k in vistos: continue
            vistos.add(k); pars.append("{{fonte:%d}}" % k)
        else: pars.append(p)
    faltam = ["{{fonte:%d}}" % k for k in range(1, n_f + 1) if k not in vistos]
    texto_i = [i_ for i_, p in enumerate(pars) if not eh_m(p) and not eh_img(p)]
    if eh_q and texto_i and (n_f or any(eh_img(p) for p in pars[texto_i[-1] + 1:])):
        # o comando da questao (ultimo paragrafo de texto) fica sempre por ultimo: fontes e figuras que vieram
        # depois dele (layout com imagem ao lado) sobem para antes dele
        ult = texto_i[-1]
        depois = pars[ult + 1:]
        pars = pars[:ult] + depois + faltam + [pars[ult]]
    else:
        pars += faltam
    item[campo] = "\n\n".join(pars)
for q in saida_q: posiciona_fontes(q, "enunciado", True)
for t in saida_t + nao_ligados: posiciona_fontes(t, "texto", False)

# recorte de revisao: pedaco da pagina original de cada questao
for q in saida_q + saida_t:
    q["recortes"] = []
    for pn, cx in sorted(((int(k), v) for k, v in q["caixas"].items())):
        x0 = min(c[0] for c in cx) - 6; y0 = min(c[1] for c in cx) - 6; x1 = max(c[2] for c in cx) + 6; y1 = max(c[3] for c in cx) + 6
        s = 110 / 72
        nome = f"{q['id'][len(PID) + 1:]}_p{pn}"
        arq = render(pn, 110, x0 * s, y0 * s, (x1 - x0) * s, (y1 - y0) * s, "jpg", os.path.join(OUT, "revisao", nome))
        q["recortes"].append(os.path.relpath(arq, OUT))

json.dump(saida_q, open(os.path.join(OUT, "questoes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump(saida_t, open(os.path.join(OUT, "textos_base.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump([{k: t[k] for k in ("id", "texto", "paginas")} for t in nao_ligados], open(os.path.join(OUT, "textos_nao_ligados.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
nums = [q["numero"] for q in saida_q]
if PENDENTES_VISAO: print("PENDENTES de transcrição por visão:", PENDENTES_VISAO)
print(f"frações empilhadas convertidas para texto: {NFRAC}")
print(f"textos-base sem questão ligada (descartados, ver textos_nao_ligados.json): {len(nao_ligados)}")
print(f"{PID}: {len(saida_q)} questões ({min(nums) if nums else '-'}–{max(nums) if nums else '-'}), {len(saida_t)} textos-base, "
      f"{sum(len(q['imagens']) for q in saida_q)} imagens, {sum(1 for q in saida_q if q['alertas'])} com alerta")
faltam = sorted(set(range(min(nums), max(nums) + 1)) - set(nums)) if nums else []
if faltam: print("números faltando:", faltam)

# glifos Type3 que o codigo nao reconheceu: folha para conferencia por visao (depois entram em _banco/glifos_ref.json)
if GLIFOS_DESCONHECIDOS:
    os.makedirs(os.path.join(OUT, "revisao"), exist_ok=True)
    lista = []; linhas_img = []
    for i_, (ass, (pn_, bx, a_)) in enumerate(sorted(GLIFOS_DESCONHECIDOS.items())):
        lista.append({"n": i_, "assinatura": ass, "pagina": pn_, "caixa": [round(v, 1) for v in bx], "H": int(a_.shape[0]), "W": int(a_.shape[1]),
                      "bits": np.packbits(a_).tobytes().hex()})
        gi = cv2.cvtColor((~a_).astype(np.uint8) * 255, cv2.COLOR_GRAY2BGR)
        sc = 34 / max(a_.shape[0], 8); gi = cv2.resize(gi, (max(1, int(a_.shape[1] * sc)), max(1, int(a_.shape[0] * sc))), interpolation=cv2.INTER_NEAREST)
        s_ = 200 / 72; x0, y0, x1, y1 = bx
        ctx = render(pn_, 200, (x0 - 40) * s_, (y0 - 8) * s_, (x1 - x0 + 80) * s_, (y1 - y0 + 16) * s_, "png")
        ci = cv2.imread(ctx)
        H_ = max(44, gi.shape[0], ci.shape[0] if ci is not None else 0)
        pad = lambda im, w: cv2.copyMakeBorder(im, 0, H_ - im.shape[0], 0, max(0, w - im.shape[1]), cv2.BORDER_CONSTANT, value=(255, 255, 255))[:, :w]
        lab = np.full((H_, 50, 3), 255, np.uint8); cv2.putText(lab, str(i_), (2, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 200), 2)
        linhas_img.append(cv2.copyMakeBorder(np.hstack([lab, pad(gi, 130), pad(ci, 320) if ci is not None else np.full((H_, 320, 3), 255, np.uint8)]), 0, 3, 0, 0, cv2.BORDER_CONSTANT, value=(180, 180, 180)))
    json.dump(lista, open(os.path.join(OUT, "revisao", "glifos_desconhecidos.json"), "w"), ensure_ascii=False)
    for k_ in range(0, len(linhas_img), 30):
        cv2.imwrite(os.path.join(OUT, "revisao", f"glifos_desconhecidos_{k_ // 30}.png"), np.vstack(linhas_img[k_:k_ + 30]))
    print(f"glifos Type3 não reconhecidos: {len(lista)} (folha em revisao/glifos_desconhecidos_*.png)")
if INVISIVEIS: print(f"palavras invisíveis descartadas (camada oculta/texto sem tinta): {sum(INVISIVEIS.values())} em {len(INVISIVEIS)} páginas")
