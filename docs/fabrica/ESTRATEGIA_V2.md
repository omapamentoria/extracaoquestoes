# Fábrica v2: extração em massa barata, sem perder qualidade (aprovada pelo Matheus em 28/11/2026)

**Por quê:** o lote 1 (ENEM 2009–2019, 44 provas) custou cerca de US$ 93, perto de US$ 2 por prova. Para as 2.385 provas
do Drive novo isso é caro demais. O gasto veio de (a) conversas enormes, relidas a cada passo, e (b) a IA lendo
página por página para corrigir símbolos e figuras. **Meta:** custo de IA perto de zero nas questões sem alerta, e só
recortes pequenos para um modelo barato nas questões com alerta.

## Regras de ouro (não mudam)

Cópia fiel, nada inventado. Gabarito só o oficial da própria prova (mesma cor), 100% igual ao relido do PDF. O incerto
não é publicado: fica marcado e explicado. Tudo o que mexe no banco publicado vira PR para o Matheus aprovar.

## Peça 1: `ferramentas_nuvem/fabrica/roda_lote.py <PID>...` (sem IA, em segundo plano, várias provas ao mesmo tempo)

Para cada prova do catálogo (`_banco/catalogo_drive2/`, campo `drive_id`):
1. Baixa a prova e o gabarito pelo ID (cache local), confere `pdfinfo` e normaliza se preciso (`normaliza_pdf.py`).
2. Extrai com `_banco/codigo/06_extrair.py` (usa as melhorias dos lotes 1-A/1-B: ramos `claude/enem-lote1-a` e
   `claude/enem-lote1-b`; junte o que for útil, sem quebrar 2009–2025).
3. **Gabarito:** leitura independente do PDF oficial (`gab_enem.py` e uma versão genérica para outras instituições).
   Tem que dar 100% igual à extração. Se não der, a prova inteira fica "vermelha" e nada dela é publicado.
4. **Casa com o banco** (`integra.py`, pelo texto, incluindo o banco antigo).
5. **Separa as questões:**
   - **prontas:** sem nenhum alerta do extrator (sem PENDENTE, `(cid:`, caracteres U+E000–U+F8FF, tabela transcrita
     automaticamente, figura suspeita), gabarito conferido e texto que casa bem;
   - **pendentes:** todo o resto. Para cada uma, grava o recorte da página (`pdftoppm` com `paginas`/`caixas`), o texto
     extraído e o motivo, em `_banco/pendentes/<lote>/<PID>-Q<n>.{png,json}`.
6. **Classifica as novas pelo vizinho mais parecido** entre as ~27 mil questões já classificadas (TF-IDF ou similar,
   só da mesma área da prova). Guarda a confiança. As de confiança baixa vão para a lista de confirmação.
7. **Publica** só as prontas (`publica.py`). Os campos `prova_completa*` só entram quando TODAS as questões da prova
   estiverem prontas. Prova com pendentes fica de fora da "prova completa" até o mutirão.
8. **Verifica** (`verifica.py`) e grava um relatório curto por lote (provas, prontas, pendentes por tipo, novas,
   já existentes, gabaritos corrigidos).

## Peça 2: mutirão das pendentes (modelo barato, lotes curtos)

`ferramentas_nuvem/fabrica/mutirao.py` monta lotes de ~30 pendentes do mesmo tipo (fórmula, tabela, símbolo...), cada
um com o recorte e o texto extraído, e instruções curtas. Uma sessão **Sonnet** (nova a cada lote) lê o lote e grava
as correções no formato de `ferramentas_nuvem/enem/correcoes/<ano>.json` (sempre com `motivo`). Depois o
`roda_lote.py` roda de novo e publica o que ficou pronto. Confirmação de classificação incerta: mesmo esquema, em
listas compactas (fim do enunciado + alternativas).

## Peça 3: como as sessões trabalham

- Sessões curtas (um lote de até ~10 provas ou um lote do mutirão) que terminam e dão lugar a uma nova.
- A sessão não lê prova por prova: roda o script, lê o relatório e só olha o que o relatório apontar.
- No máximo 2 sessões ao mesmo tempo.

## Teste: ENEM 2000–2008 (9 provas de 63 questões, P7506–P7523)

ID_BASE 180000, PARTE 36, REFAZER `comentarios_a_refazer_2026-11_enem2000a2008.json`. Ramos: `claude/fabrica-v2`
(extracaoquestoes, a partir de `claude/fabrica-catalogo`) e `claude/enem-2000a2008-completo` (Banco-de-questoes, a
partir de `claude/busy-tesla-cibdm3`). Um PR, sem merge. No relatório: quanto ficou pronto sem IA, quantas pendentes
por tipo, e o tempo de cada etapa.
