# Lote 1 da fábrica: ENEM 2000–2019 (manual das sessões)

Aprovado pelo Matheus em 27/11/2026. Use o mesmo método de `docs/enem/SESSAO_ANO.md` (leia inteiro antes), com as
diferenças abaixo. Leia também `CLAUDE.md` e a seção 11 de `docs/HANDOFF-conta-mapa.md`.

## Divisão (no máximo 2 sessões ao mesmo tempo)

| Sessão | Anos | ID_BASE | PARTE | REFAZER | Ramo extracaoquestoes | Ramo Banco-de-questoes |
|---|---|---|---|---|---|---|
| A | 2015–2019 | 160000 | 34 | comentarios_a_refazer_2026-11_enem2015a2019.json | claude/enem-lote1-a | claude/enem-2015a2019-completo |
| B | 2009–2014 | 170000 | 35 | comentarios_a_refazer_2026-11_enem2009a2014.json | claude/enem-lote1-b | claude/enem-2009a2014-completo |
| (depois) | 2000–2008 | 180000 | 36 | comentarios_a_refazer_2026-11_enem2000a2008.json | claude/enem-lote1-c | claude/enem-2000a2008-completo |

O ramo do extracaoquestoes sai de `claude/fabrica-catalogo`. Um PR só por sessão, para `claude/busy-tesla-cibdm3`
(**não faça merge**; o Matheus aprova). Ids novos: comece em ID_BASE e não passe de ID_BASE + 9999.

## O que muda em relação ao SESSAO_ANO

1. **Os códigos de PDF já existem** (catálogo automático, `_banco/catalogo_drive2/drive2_enem.json`, P7506–P7619;
   campo `drive_id` = ID no Drive para o `curl`). Não crie códigos novos. Para cada ano, grave
   `_banco/catalogo_drive2/<ano>.json` com as entradas (prova e gabarito) **com os mesmos códigos**, corrigindo o que o
   script estimou: `edicao` (mesmo texto que o banco já usa nesse ano), `dia`, `caderno` (cor, vista na 1ª página),
   `gabarito_ids`. O `catalogo.py` dá preferência ao `<ano>.json` sobre o `drive2_enem.json`.
2. **O gabarito ligado pelo script é só uma estimativa.** Confira pelo conteúdo (cor e dia no cabeçalho do gabarito). A
   regra de ouro continua: só o gabarito oficial da MESMA cor. Casos já conhecidos:
   - 2010 regular (P7537/P7539): gabarito não lido ou ausente na pasta. Procure o oficial no Drive novo
     (`docs/enem/drive2_enem.json`) ou no Drive antigo (`_banco/catalogo_debug.json`, IDs em
     `ferramentas_nuvem/mapa_drive.json`).
   - A pasta 2013/ENEM tem arquivos com nome "2012" (P7561/P7563): descubra pelo conteúdo de que ano são; se forem
     repetidos do 2012, não extraia duas vezes.
   - O campo `ja_no_drive_antigo` diz que o PDF é idêntico a um do Drive antigo: as questões provavelmente já estão no
     banco (o `integra.py` casa pelo texto e mantém id, comentário e classificação).
3. **Formato antigo:** de 2009 a 2016 o dia 1 é Humanas + Natureza (1–90) e o dia 2 é Linguagens + Matemática (91–180,
   com 91–95 do idioma). Ajuste as faixas de área (`"_area"` em `correcoes/<ano>.json`) e o tratamento do idioma
   (`gab_enem.py` lê os pares inglês/espanhol só até a questão 5: generalize com cuidado, sem quebrar 2020–2025).
   2000–2008: prova única de 63 questões, sem cor.
4. **Relatório:** `docs/enem/<ano>.md` por ano, no seu ramo. No fim, responda com um resumo curto: provas, cores,
   questões (novas / já existentes / do banco antigo), gabaritos corrigidos, link do PR, pendências.

Seja econômico: trabalho pesado em scripts e em segundo plano; não leia arquivos grandes inteiros.
