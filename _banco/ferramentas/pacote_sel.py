# uso: pacote_sel.py <pasta_saida> "<titulo>" PID... -> pagina de revisao so com as questoes que pedem olho:
# com alerta, transcritas por visao e uma amostra aleatoria de 5 por prova (index_rev3.html + dados.json + imagens web)
import json, sys, os, glob, shutil, random, cv2
out, titulo, pids = sys.argv[1], sys.argv[2], sys.argv[3:]
os.makedirs(out, exist_ok=True)
B = os.path.expanduser('~/mnt/BM/_banco'); C = {d['id']: d for d in json.load(open(B + '/catalogo_debug.json', encoding='utf-8'))}
def web(src, nome, maxw=900, q=82):
    im = cv2.imread(src)
    if im is None: return None
    if im.shape[1] > maxw: im = cv2.resize(im, (maxw, int(im.shape[0] * maxw / im.shape[1])), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(out, nome), im, [cv2.IMWRITE_JPEG_QUALITY, q]); return nome
provas = []
for pid in pids:
    d = glob.glob(f'{B}/questoes/*/*/{pid}')[0]; P = C[pid]
    q = json.load(open(d + '/questoes.json')); t = json.load(open(d + '/textos_base.json'))
    rnd = random.Random(pid)
    com_alerta = [x for x in q if x.get('alertas')]
    resto = [x for x in q if not x.get('alertas')]
    amostra = rnd.sample(resto, min(5, len(resto)))
    for x in amostra: x['alertas'] = ['(amostra aleatória, sem alerta)']
    sel_ids = {x['id'] for x in com_alerta + amostra}
    sel = [x for x in q if x['id'] in sel_ids]
    tb_ids = {i for x in sel for i in (x.get('textos_base_ids') or [])}
    tsel = [x for x in t if x['id'] in tb_ids]
    for x in sel + tsel:
        for im in x['imagens']:
            im['web'] = web(os.path.join(d, im['arquivo']), f"{pid}_{os.path.basename(im['arquivo']).rsplit('.', 1)[0]}.jpg")
        x['recortes_web'] = [web(os.path.join(d, r), f"{pid}_{os.path.basename(r).rsplit('.', 1)[0]}.jpg", maxw=700, q=70) for r in x.get('recortes', [])]
    tit = f"{P['vestibular']} {P['ano']} — {P.get('edicao') or ''} {('dia ' + P['dia']) if P.get('dia') else ''}".replace('  ', ' ')
    provas.append({'id': pid, 'titulo': tit, 'arquivo': P['arquivo'], 'questoes': sel, 'textos_base': tsel, 'nao_ligados': []})
    print(pid, len(sel), 'questões na página')
json.dump({'provas': provas}, open(os.path.join(out, 'dados.json'), 'w'), ensure_ascii=False)
html = open(os.path.join(B, 'ferramentas', 'index_rev3.html'), encoding='utf-8').read()
html = html.replace('<title>Piloto 2 ENEM e SSA</title>', f'<title>{titulo}</title>').replace('Piloto 2 ENEM e SSA — Banco MAPA', f'{titulo} — Banco MAPA')
html = html.replace('Confira se o texto está igual', 'Aqui estão só as questões com alerta, as digitadas lendo a imagem e 5 sorteadas por prova. Confira se o texto está igual')
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
fs = os.listdir(out); print(len(fs), 'arquivos', round(sum(os.path.getsize(os.path.join(out, f)) for f in fs) / 1e6, 1), 'MB')
