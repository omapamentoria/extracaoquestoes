# Banco MAPA de Questões — plano e decisões

Atualizado em 26/09/2026.

## Decisões

* Sem API da Anthropic. Tudo feito dentro da assinatura Claude Pro (Cowork/Claude Code). Max só se precisar, nas resoluções.
* Escopo atual: extrair as questões + gabarito. Classificação por assunto e resolução ficam para depois; os campos já existem no esquema.
* Fonte: pasta local `C:\BM`, com duas pastas dentro: `DRIVE ENEM + VEST - SIGAM @WAGNERNAMED` (Drive completo, todas as partes do zip) e `O Mapa Mentoria` (ENEM + SSA). O Matheus decidiu usar todo material que contenha questões (provas oficiais, simulados, apostilas).
* Método: Python extrai o que dá de graça; o Claude (visão) entra nas páginas problemáticas; validações automáticas marcam o que precisa de revisão.
* Ordem de prioridade: ENEM → SSA → simulados ENEM → FUVEST/UNICAMP/UERJ/UNESP → demais vestibulares → compilações (deduplicadas contra as provas oficiais). A FPS entra depois (o Matheus ainda vai conseguir o material).
* Regra de inventário: listar pasta por pasta e conferir cada subpasta antes de afirmar que algo falta.
* Resultados (decisão de 28/09/2026, sessão na nuvem): guardados neste repositório GitHub, em `_banco/questoes/<vestibular>/<ano>/<id_prova>/`, com um commit por lote (por etapas).

## Catálogo (feito em 26/09/2026) — `C:\BM\_banco\catalogo.xlsx`

4.237 PDFs no total: 1.834 a extrair, 1.291 gabaritos/resoluções pareados, 494 duplicatas e 618 sem questões.

| Grupo | Prioridade | A extrair | Páginas | Questões (estimativa) |
|---|---|---|---|---|
| ENEM (1998–2025, com PPL, reaplicações e COP30) | 1 | 89 | 2.930 | ~6.800 |
| SSA (2015–2021 e 2025) | 2 | 46 | 1.472 | ~1.900 |
| Simulados ENEM (Bernoulli, SAS, Somos, Poliedro, Hexag, FB, Objetivo) | 3 | 423 | 14.489 | ~37.000 |
| Simulados SSA (SAS) | 3 | 8 | 229 | ~330 |
| FUVEST / UNICAMP / UERJ / UNESP | 4 | 263 | 6.174 | ~4.000 |
| Demais (FATEC, FAMERP, FAMEMA, UEL, UFGD, UFU, UFMS, UNEMAT, Unifesp, USS) | 5 | 266 | 5.286 | ~7.800 |
| Simulados FUVEST/UNICAMP/UERJ/UNESP | 6 | 25 | 598 | ~900 |
| Compilações (por assunto, habilidades, pré-teste etc.) | 7 | 391 | 14.608 | ~5.800 |
| Apostilas e livros didáticos | 8 | 289 | 27.509 | ~10.900 |
| ENCCEJA | 9–10 | 34 | 642 | ~960 |

A estimativa de questões é uma contagem automática, só para planejar. Só as provas oficiais + simulados já passam de 60 mil questões.

## Achados do diagnóstico

* 210 arquivos a extrair têm texto ruim (corrompido ou só imagem) e vão precisar de visão/OCR. Nas provas prioritárias: ENEM 2010 1º dia (letras deslocadas), ENEM 2013 e 2014 regular (só imagem), ENEM PPL 2014 e 2016, ENCCEJA 2017, Somos 2022, Bernoulli 2024 nº 05 e 06.
* A pasta `O Mapa Mentoria/ENEM MATERIAL` é quase toda cópia do Drive (marcada como duplicata). Ela tem de exclusivo os simulados SAS 2014–2020.
* ENEM: várias cores do mesmo caderno estão no acervo. O catálogo escolhe uma cor principal e marca as outras como "mesma prova". O gabarito tem de ser o da mesma cor.
* FUVEST/UNICAMP/UNESP 2023–2025: o arquivo sem "_prova" no nome é a resolução comentada (traz as questões + respostas).
* UEL 2023: diagramação em 2 colunas; a extração simples mistura as questões. Precisa de extração por coluna.
* UFGD 2012: fórmulas somem no texto (são imagens). Essas questões precisam de visão.
* Simulado Bernoulli 2026: texto limpo. O gabarito comentado traz resoluções que podem ser importadas.

## Esquema de cada questão

* Identificação: id, instituição/banca, vestibular, tipo de fonte (prova oficial / simulado / apostila / compilado), ano, edição/aplicação (regular, PPL, reaplicação, digital), fase/etapa, dia, caderno/cor/tipo, número original.
* Conteúdo: área, disciplina, opção de idioma, texto-base compartilhado (id), enunciado (Markdown + LaTeX), alternativas, imagens (arquivos), formato (múltipla escolha, V/F, somatória, discursiva).
* Resposta: gabarito, anulada, resolução original (se houver).
* Rastreabilidade: arquivo de origem (id do catálogo), página(s), status de revisão.
* Futuro: assunto, subassunto, habilidade ENEM, dificuldade, resolução MAPA, hash para deduplicação.
