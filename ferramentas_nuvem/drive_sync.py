# Lista e baixa pastas publicas do Google Drive ("qualquer pessoa com o link").
# Uso:
#   python3 drive_sync.py listar <folder_id> <saida.json> [prefixo]
#   python3 drive_sync.py baixar <lista.json> <destino> [filtro_regex]
import json, os, re, sys, time, html, urllib.request, concurrent.futures as cf

UA = {"User-Agent": "Mozilla/5.0"}
ENTRY = re.compile(r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)".*?flip-entry-title">([^<]*)<', re.S)


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 ** i)


def listar(folder_id, prefixo=""):
    out = []
    page = get(f"https://drive.google.com/embeddedfolderview?id={folder_id}").decode("utf-8", "replace")
    for fid, href, nome in ENTRY.findall(page):
        nome = html.unescape(nome).strip()
        caminho = f"{prefixo}/{nome}" if prefixo else nome
        if "/folders/" in href:
            out += listar(fid, caminho)
        else:
            out.append({"id": fid, "path": caminho})
    return out


def baixar_um(item, destino):
    alvo = os.path.join(destino, item["path"])
    if os.path.exists(alvo) and os.path.getsize(alvo) > 0:
        return "ok"
    os.makedirs(os.path.dirname(alvo), exist_ok=True)
    data = get(f"https://drive.usercontent.google.com/download?id={item['id']}&export=download&confirm=t")
    if data[:15].lower().startswith(b"<!doctype html"):
        return "html"
    with open(alvo + ".part", "wb") as f:
        f.write(data)
    os.replace(alvo + ".part", alvo)
    return "ok"


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "listar":
        itens = listar(sys.argv[2], sys.argv[4] if len(sys.argv) > 4 else "")
        json.dump(itens, open(sys.argv[3], "w"), ensure_ascii=False, indent=0)
        print(len(itens), "arquivos")
    elif cmd == "baixar":
        itens = json.load(open(sys.argv[2]))
        if len(sys.argv) > 4:
            itens = [i for i in itens if re.search(sys.argv[4], i["path"])]
        falhas = []
        with cf.ThreadPoolExecutor(8) as ex:
            futs = {ex.submit(baixar_um, i, sys.argv[3]): i for i in itens}
            for f in cf.as_completed(futs):
                try:
                    r = f.result()
                except Exception as e:
                    r = repr(e)
                if r != "ok":
                    falhas.append((futs[f]["path"], r))
        print(len(itens) - len(falhas), "baixados;", len(falhas), "falhas")
        for p, r in falhas[:30]:
            print("FALHA", r, p)
