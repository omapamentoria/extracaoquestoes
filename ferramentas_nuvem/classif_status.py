# Status da classificacao (Fase 5b): questoes classificadas, tokens dos ajudantes, custo estimado, tempo e previsao.
# Os tokens vem de unificacao/classif/uso.json (anotados a cada ajudante que termina).
# Custo: estimativa pelo preco de API (Sonnet 5.5 US$ 2 / 10 por milhao; Haiku 4.5 US$ 1 / 5), supondo ~95% entrada.
import json, os, glob, datetime

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = os.path.join(R, "unificacao", "classif")
uso = json.load(open(os.path.join(C, "uso.json")))
lotes = sorted(glob.glob(os.path.join(C, "lotes", "lote_*.json")))
feitos = [f for f in lotes if os.path.exists(os.path.join(C, "respostas", os.path.basename(f)))]
n_tot = sum(len(json.load(open(f))) for f in lotes); n_feito = sum(len(json.load(open(f))) for f in feitos)
preco = {"sonnet": 0.95 * 2 + 0.05 * 10, "haiku": 0.95 * 1 + 0.05 * 5}           # US$ por milhao de tokens
tok = sum(c["tokens"] for c in uso["chamadas"]); usd = sum(c["tokens"] / 1e6 * preco[c["modelo"]] for c in uso["chamadas"])
ini = datetime.datetime.fromisoformat(uso["inicio"].replace("Z", "+00:00")); agora = datetime.datetime.now(datetime.timezone.utc)
dur = agora - ini; h = dur.total_seconds() / 3600
tok_por_lote = sum(c["tokens"] for c in uso["chamadas"] if c["modelo"] == "sonnet") / max(1, sum(len(c["lotes"]) for c in uso["chamadas"] if c["modelo"] == "sonnet"))
faltam = len(lotes) - len(feitos)
ritmo = len(feitos) / h if h > 0 else 0
print(f"Questões classificadas: {n_feito:,} de {n_tot:,} ({100 * n_feito / n_tot:.0f}%) — lotes {len(feitos)} de {len(lotes)}".replace(",", "."))
print(f"Tokens usados pelos ajudantes: {tok / 1e6:.2f} milhões (~{tok_por_lote / 1e3:.0f} mil por lote de 100)")
print(f"Custo estimado (preço de API): US$ {usd:.2f}; previsão para o total: US$ {usd + faltam * tok_por_lote / 1e6 * preco['sonnet']:.0f}")
print(f"Tempo decorrido: {int(h)}h{int(dur.total_seconds() // 60 % 60):02d}; ritmo {ritmo:.0f} lotes/h; "
      f"previsão para terminar: {'—' if not ritmo else f'{faltam / ritmo:.1f} h'}")
