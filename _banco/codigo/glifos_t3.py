def _forma(a):   # tamanho do glifo para a assinatura (glifo com mais de 255 px de lado nao cabe em bytes())
    return bytes(a.shape) if max(a.shape) < 256 else str(a.shape).encode()
# Carregado pelo 06_extrair.py (exec no mesmo espaco de nomes: usa os, re, json, np, cv2, hashlib e B de la).
# ------------------------------------------------------------------ glifos de fonte Type3 (letra desenhada como imagem)
# Alguns PDFs (ex.: FUVEST) escrevem hifen, "x" de multiplicacao, "~", letras de formula etc. numa fonte Type3 cujos
# caracteres sao pequenas imagens, sem tabela de texto: o PDF so diz "(cid:2)". O codigo le a imagem de cada glifo e
# compara com a tabela de glifos ja identificados (_banco/glifos_ref.json, conferida por visao). Glifo reconhecido
# vira texto; glifo desconhecido continua tinta (e a questao fica PENDENTE, como qualquer trecho desenhado).
from pdfminer.pdftypes import resolve1 as _res1
from pdfplumber.utils.text import WordExtractor
GLIFOS_REF_P = os.path.join(B, "glifos_ref.json")
GLIFOS_REF = json.load(open(GLIFOS_REF_P, encoding="utf-8")) if os.path.exists(GLIFOS_REF_P) else []
def _norm_glifo(a, N=24):
    ys, xs = np.nonzero(a)
    if len(ys) == 0: return None
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    return cv2.resize(a, (N, N), interpolation=cv2.INTER_AREA) > 0.35, a.shape
for _g in GLIFOS_REF:
    _a = np.unpackbits(np.frombuffer(bytes.fromhex(_g["bits"]), np.uint8))[:_g["H"] * _g["W"]].reshape(_g["H"], _g["W"]).astype(bool)
    _g["_n"], _g["_shape"] = _norm_glifo(_a)
GLIFOS_DESCONHECIDOS = {}      # assinatura -> (pagina, caixa, imagem) para a folha de conferencia
BARRAS_T3 = {}
T3_FORMULA = {}                # caixas de simbolos de formula lidos de glifos Type3 (a questao fica "conferir")                 # barras Type3 que sao traco de fracao/sobrelinha: entram como retangulos em fracoes()
def _decode_glifo(data):
    m = re.match(rb"\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+d1", data)
    if not m: return None
    wx, _, llx, lly, urx, ury = [float(x) for x in m.groups()]
    i_ = data.find(b"BI"); j_ = data.find(b"ID", i_)
    if i_ < 0 or j_ < 0: return None
    hdr = data[i_ + 2:j_].decode("latin1")
    mw = re.search(r"/W(?:idth)?\s+(\d+)", hdr); mh = re.search(r"/H(?:eight)?\s+(\d+)", hdr)
    if not mw or not mh: return None
    W_, H_ = int(mw.group(1)), int(mh.group(1)); rb = (W_ + 7) // 8
    raw = data[j_ + 3:j_ + 3 + rb * H_]
    if len(raw) < rb * H_: return None
    bits = np.unpackbits(np.frombuffer(raw, np.uint8)).reshape(H_, rb * 8)[:, :W_].astype(bool)
    dec = re.search(r"/D(?:ecode)?\s*\[\s*1\s+0\s*\]", hdr) is not None
    return {"wx": wx, "bbox": (llx, lly, urx, ury), "img": bits if dec else ~bits}
def _fontes_t3(page_obj):
    out = []
    try:
        res = _res1(page_obj.resources) or {}
        fonts = _res1(res.get("Font", {})) or {}
    except Exception:
        return out
    for v in fonts.values():
        v = _res1(v)
        if str(_res1(v.get("Subtype"))) != "/'Type3'": continue
        enc = _res1(v.get("Encoding")) or {}
        dif = _res1(enc.get("Differences", [])) if isinstance(enc, dict) else []
        cod = {}; c_ = 0
        for x in dif:
            x = _res1(x)
            if isinstance(x, int): c_ = x
            else: cod[c_] = getattr(x, "name", str(x)); c_ += 1
        cp = _res1(v.get("CharProcs")) or {}
        gl = {}
        for c_, nome in cod.items():
            st_ = cp.get(nome)
            if st_ is None: continue
            try: g = _decode_glifo(_res1(st_).get_data())
            except Exception: g = None
            if g: gl[c_] = g
        out.append(gl)
    return out
def _reconhece(a):
    nn = _norm_glifo(a)
    if nn is None: return None
    n_, shp = nn
    melhor = None
    for g in GLIFOS_REF:
        # proporcao parecida (hifen x barra de fracao se distinguem pelo contexto, em _barra)
        if abs(np.log((shp[0] / shp[1]) / (g["_shape"][0] / g["_shape"][1]))) > 0.35: continue
        d = (n_ != g["_n"]).mean()
        if melhor is None or d < melhor[0]: melhor = (d, g)
    if melhor and melhor[0] < 0.10: return melhor[1]
    return None
def _acima(bx, normais, outros):
    """ha texto logo acima da barra, dentro da largura dela (numerador de fracao)?"""
    x0, y0, x1, y1 = bx
    return any(n["x0"] >= x0 - 1 and n["x1"] <= x1 + 1 and -1 <= y0 - n["bottom"] < 3 for n in normais) or \
           any(b[0] >= x0 - 1 and b[2] <= x1 + 1 and -1 <= y0 - b[3] < 3.5 for b in outros)
def _barra(c, bx, viz, normais, outros=()):
    """barra de fonte Type3: hifen, travessao, sinal de menos ou traco de fracao/sobrelinha (None = fica como tinta)"""
    x0, y0, x1, y1 = bx; lg = x1 - x0
    # letras logo abaixo/acima da barra, cobertas por ela (sobrelinha de segmento, traco de fracao): nao e texto
    if any(n["x0"] >= x0 - 1 and n["x1"] <= x1 + 1 and 0 <= n["top"] - y1 < 4 for n in normais): return None
    if any(n["x0"] >= x0 - 1 and n["x1"] <= x1 + 1 and 0 <= y0 - n["bottom"] < 4 for n in normais): return None
    # idem com letras que tambem sao glifos Type3 (tinta da letra logo abaixo da barra)
    if any(b[0] >= x0 - 1 and b[2] <= x1 + 1 and (0 <= b[1] - y1 < 4 or 0 <= y0 - b[3] < 4) and b != bx for b in outros): return None
    tam = viz[0]["size"] if viz else 10
    esq = [n for n in viz if n["x1"] <= c["x0"] + 0.5]; dir_ = [n for n in viz if n["x0"] >= c["x1"] - 0.5]
    ge = (c["x0"] - max(n["x1"] for n in esq)) if esq else 99
    gd = (min(n["x0"] for n in dir_) - c["x1"]) if dir_ else 99
    ce = max(esq, key=lambda n: n["x1"])["text"] if esq else ""
    cd = min(dir_, key=lambda n: n["x0"])["text"] if dir_ else ""
    if lg >= 0.85 * tam: return "—"
    if ge < 0.15 * tam and gd < 0.15 * tam and ce.isalpha() and cd.isalpha(): return "-"
    if re.match(r"[\d(]", cd) and (ge > 0.15 * tam or ce in ("", "(", "=", "+", "×", "[")) and gd < 0.2 * tam: return "−"
    if ge > 0.15 * tam and gd > 0.15 * tam and lg >= 0.4 * tam: return "–"
    return "-"
def glifos_t3(page_orig, chars):
    """converte os caracteres de fonte Type3 reconhecidos em texto (na lista chars, no lugar)"""
    t3 = [c for c in chars if c["text"].startswith("(cid:") and c["size"] < 1]
    if not t3: return
    fontes = _fontes_t3(page_orig.page_obj)
    normais = [c for c in chars if not (c["text"].startswith("(cid:") and c["size"] < 1) and c.get("upright", True)]
    info = []
    for c in t3:
        cod = int(c["text"][5:-1]); larg = c["x1"] - c["x0"]
        cands = [f[cod] for f in fontes if cod in f and abs(f[cod]["wx"] * c["size"] - larg) < 0.05]
        if not cands: continue
        g = cands[0]; s_ = c["size"]
        vira = (c.get("matrix") or (1, 0, 0, 1))[3] < 0
        a = g["img"][::-1] if vira else g["img"]
        llx, lly, urx, ury = g["bbox"]
        # linha de base: pela matriz do caractere (o "top" que o pdfminer calcula para Type3 nao e confiavel)
        mt = c.get("matrix")
        base = (page_orig.height - mt[5]) if mt else c["top"]
        y0, y1 = sorted([base + lly * s_, base + ury * s_]) if vira else sorted([base - ury * s_, base - lly * s_])
        x0i, x1i = c["x0"] + llx * s_, c["x0"] + urx * s_
        ref = _reconhece(a)
        if ref is None:
            ass = hashlib.md5(a.tobytes() + _forma(a)).hexdigest()[:10]
            GLIFOS_DESCONHECIDOS.setdefault(ass, (page_orig.page_number, (x0i, y0, x1i, y1), a))
            continue
        info.append((c, ref, base, x0i, y0, x1i, y1, larg))
    # barra feita de varios pedacos encostados (sobrelinha de segmento "BC" desenhada com 3 tracinhos): vira uma barra so
    barras = sorted([i_ for i_ in info if i_[1]["char"] == "BAR"], key=lambda i_: (round(i_[4], 0), i_[3]))
    grupos_b = []
    for i_ in barras:
        g_ = grupos_b[-1] if grupos_b else None
        if g_ and abs(g_[-1][4] - i_[4]) < 0.6 and abs(g_[-1][6] - i_[6]) < 0.6 and i_[3] - g_[-1][5] < 0.8: g_.append(i_)
        else: grupos_b.append([i_])
    juntas_b = set()
    for g_ in grupos_b:
        if len(g_) < 2: continue
        X0, Y0, X1, Y1 = min(i_[3] for i_ in g_), min(i_[4] for i_ in g_), max(i_[5] for i_ in g_), max(i_[6] for i_ in g_)
        letras_ = [(i_[3], i_[4], i_[5], i_[6]) for i_ in info if i_[1]["char"] != "BAR"]
        sob = any(n["x0"] >= X0 - 1 and n["x1"] <= X1 + 1 and 0 <= n["top"] - Y1 < 4 for n in normais) or \
              any(b[0] >= X0 - 1 and b[2] <= X1 + 1 and 0 <= b[1] - Y1 < 4 for b in letras_)
        if sob:
            # sem numerador em cima = sobrelinha de segmento (nunca fracao)
            BARRAS_T3.setdefault(page_orig.page_number, []).append({"x0": X0, "x1": X1, "top": Y0, "bottom": Y1, "width": X1 - X0, "height": Y1 - Y0, "object_type": "rect",
                                                                    "so_sobrelinha": not _acima((X0, Y0, X1, Y1), normais, letras_)})
            juntas_b |= {id(i_[0]) for i_ in g_}
            T3_FORMULA.setdefault(page_orig.page_number, []).append((X0, Y0 - 1, X1, Y1 + 8, True))
    # sinal de raiz: a barra de cima (vinculo) comeca na ponta do "√" -> a barra nao e texto nem fracao
    raizes = [(x1i, y0) for c, ref, base, x0i, y0, x1i, y1, larg in info if ref["char"] == "√"]
    for c, ref, base, x0i, y0, x1i, y1, larg in info:
        # vizinho normal na mesma linha de base: copia tamanho/fonte (para a palavra nao se partir)
        viz = [n for n in normais if abs((n["bottom"] - 0.22 * n["size"]) - base) < 0.3 * n["size"] + 1
               and min(abs(n["x1"] - c["x0"]), abs(c["x1"] - n["x0"])) < 2.5 * n["size"]]
        viz.sort(key=lambda n: min(abs(n["x1"] - c["x0"]), abs(c["x1"] - n["x0"])))
        ch = ref["char"]
        if id(c) in juntas_b: continue
        if ch == "BAR":
            if any(abs(x0i - rx) < 2.5 and abs(y0 - ry) < 3 for rx, ry in raizes):
                continue       # vinculo da raiz: a tinta fica apagada junto com o texto de baixo
            ch = _barra(c, (x0i, y0, x1i, y1), viz, normais, [(i_[3], i_[4], i_[5], i_[6]) for i_ in info if i_[1]["char"] != "BAR"])
            if ch is None:
                outros_ = [(i_[3], i_[4], i_[5], i_[6]) for i_ in info if i_[1]["char"] != "BAR"]
                BARRAS_T3.setdefault(page_orig.page_number, []).append({"x0": x0i, "x1": x1i, "top": y0, "bottom": y1, "width": x1i - x0i, "height": y1 - y0, "object_type": "rect",
                                                                        "so_sobrelinha": not _acima((x0i, y0, x1i, y1), normais, outros_)})
                continue
        if viz:
            n = viz[0]; tam = n["size"]; fn = n["fontname"]; top = n["top"]; bot = n["bottom"]
        else:
            h_ = y1 - y0
            tam = h_ / 0.7 if re.fullmatch(r"[0-9A-ZbdfhklΔλ()\[\]]", ch) else h_ / 0.48 if re.fullmatch(r"[a-z]", ch) else 10
            tam = min(max(tam, 5), 16); fn = "T3"; top = base - 0.78 * tam; bot = base + 0.22 * tam
        if ch == "√": top = min(top, y0 - 0.5)
        if ref["estilo"] == "i" or ch in "×≈=+−√Δλ()[]" or not re.fullmatch(r"[-–—,.;:!?]", ch):
            if not (ch.isalpha() and ref["estilo"] != "i" and viz):     # letra comum no meio do texto nao e formula
                # grave: letra de formula (italico), raiz, acento solto ou simbolo sem vizinho na linha (expoente, indice)
                grave = ref["estilo"] == "i" or ch in "√\u0302" or not viz
                T3_FORMULA.setdefault(page_orig.page_number, []).append((c["x0"], top, c["x0"] + max(larg, 0.3), bot, grave))
        if ref["estilo"] == "i" and "Italic" not in fn: fn = fn + "-Italic"
        if ref["estilo"] == "b" and "Bold" not in fn: fn = fn + "-Bold"
        c.update({"text": ch, "size": tam, "fontname": fn, "top": top, "bottom": bot, "upright": True, "x1": c["x0"] + max(larg, 0.3)})

# ------------------------------------------------------------------ "(cid:N)" de fonte comum sem tabela de texto
# (ex.: seta de reacao nuclear, marcador de lista): renderiza o caractere e compara com a mesma tabela de glifos
_CID_CACHE = {}
def glifos_cid(page_orig, chars):
    for c in chars:
        if not (c["text"].startswith("(cid:") and c["size"] >= 1 and c.get("upright", True)): continue
        # (o mesmo nome de fonte pode esconder subconjuntos diferentes: o mesmo codigo e "(" num e "+" noutro ->
        #  a chave inclui tamanho e largura do caractere)
        chave = (c["fontname"], c["text"], round(c["size"], 1), round(c["x1"] - c["x0"], 1))
        if chave not in _CID_CACHE:
            ref = None
            try:
                dpi = 600; s_ = dpi / 72
                x, y = int(c["x0"] * s_), int(c["top"] * s_); w_, h_ = max(2, int((c["x1"] - c["x0"]) * s_)), max(2, int((c["bottom"] - c["top"]) * s_))
                base_ = os.path.join(TMP, f"_cid_{PID}_{os.getpid()}")
                subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page_orig.page_number), "-l", str(page_orig.page_number), "-singlefile", "-gray",
                                "-x", str(x), "-y", str(y), "-W", str(w_), "-H", str(h_), "-png", PDF, base_], check=True, capture_output=True)
                im_ = cv2.imread(base_ + ".png", cv2.IMREAD_GRAYSCALE)
                if im_ is not None:
                    a = im_ < 128
                    if a.any():
                        ref = _reconhece(a)
                        if ref is None:
                            ys_, xs_ = np.nonzero(a)
                            a2 = a[ys_.min():ys_.max() + 1, xs_.min():xs_.max() + 1]
                            GLIFOS_DESCONHECIDOS.setdefault("cid-" + hashlib.md5(a2.tobytes() + _forma(a2)).hexdigest()[:8],
                                                            (page_orig.page_number, (c["x0"], c["top"], c["x1"], c["bottom"]), a2))
            except Exception:
                ref = None
            _CID_CACHE[chave] = ref
        ref = _CID_CACHE[chave]
        if ref is None: continue
        ch_ = ref["char"]
        if ch_ == "BAR":
            # traco curto de fonte de simbolos: sinal de menos antes de numero ("−1"), senao hifen; traco longo fica tinta
            if c["x1"] - c["x0"] > 0.7 * c["size"]: continue
            prox_ = [o for o in chars if o is not c and o["x0"] >= c["x1"] - 0.5 and o["x0"] - c["x1"] < 0.4 * c["size"]
                     and abs(o["bottom"] - c["bottom"]) < 0.5 * c["size"]]
            ch_ = "−" if prox_ and re.match(r"\d", min(prox_, key=lambda o: o["x0"])["text"]) else "-"
        c["text"] = ch_
        T3_FORMULA.setdefault(page_orig.page_number, []).append((c["x0"], c["top"], c["x1"], c["bottom"], False))   # "conferir"
CID_RESOLVIDOS = {}
