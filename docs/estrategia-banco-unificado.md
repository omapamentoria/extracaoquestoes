# Banco MAPA unificado — estratégia (30/09/2026)

Juntar as questões prontas da extração nova ao banco antigo que já está na plataforma, sem perder as questões
antigas nem os gabaritos comentados.

## O que existe hoje

**Banco antigo** — repositório `omapamentoria/Banco-de-questoes`
* 5.288 questões comentadas (ENEM 4.099, SSA 830, FPS 359), ids entre 1 e 10.217, 1.087 imagens em `imagens/`.
* Texto vindo de sites (memorizevestibular), sem parágrafos, sem fórmulas; cada questão tem o comentário completo
  (raciocínio, correta, incorretas, quadro-resumo, "leve para a prova", flashcards), tema_n1..n4 e nota de revisão.
* É o que a plataforma lê: a função `question-bank-sync` do `omapa` lê `final/partes/*.json` do ramo padrão e faz
  upsert na tabela `questoes` por `id`. **Um arquivo que some do repositório arquiva as questões dele.** Imagens são
  servidas de `imagens/` do mesmo repositório (`question-bank-image`).

**Banco novo** — `extracaoquestoes` + `banco-simulados` + `banco-vestibulares` + `banco-demais`
* 60.319 questões; 41.871 prontas (35.522 sem nenhum alerta + 6.349 com alerta leve). Ver `banco-contagem.md`.
* Cópia fiel do PDF: parágrafos, negrito, tabelas, fórmulas em LaTeX, figura na posição certa (`{{img:k}}`),
  fontes separadas (`{{fonte:n}}`), gabarito oficial. Sem comentário e sem classificação.

**Sobreposição** (comparação do texto de enunciado + alternativas, 30/09/2026)

| Banco antigo | Igual no novo | Parecida no novo | Só no antigo |
|---|---:|---:|---:|
| ENEM (4.099) | 2.730 | 769 | 600 |
| SSA (830) | 220 | 161 | 449 |
| FPS (359) | 0 | 0 | 359 |
| **Total (5.288)** | **2.950** | **930** | **1.408** |

"Parecida" costuma ser a mesma questão com diferença de extração (ex.: a nova veio por OCR e perdeu uma alternativa).

## Regras

1. **Nenhuma questão antiga sai.** O id antigo continua o mesmo, com o comentário, os flashcards e a nota.
2. **Questão repetida vira uma só**, com o id e o comentário antigos. Só o texto (enunciado, alternativas, imagens)
   pode vir da extração nova, e só quando a nova for melhor.
3. **Questão nova ganha id a partir de 100.001**, fixo para sempre (tabela `ids_novos.json`: `P2605-Q091 → 100001`).
4. **Nada é apagado nem renomeado em `final/partes/`** (a sincronização arquivaria as questões). O banco novo entra
   em arquivos novos (`banco_parte_07.json` em diante, até 1.000 questões cada).

## Qual extração fica, quando a questão se repete

Automático, com o que o código consegue medir:

| Situação | Fica |
|---|---|
| A nova tem alerta grave, PENDENTE, OCR ou alternativa faltando | antiga |
| Gabaritos diferentes | antiga, e o par vai para revisão humana |
| A antiga tem imagem e a nova não (ou vice-versa) | a que tem a imagem, e o par vai para revisão |
| A nova está pronta (sem alerta) e a antiga tem texto emendado, fonte no meio do enunciado ou alternativas grudadas | nova |
| Empate | antiga (já foi revisada e comentada) |

Quando o texto troca, o comentário continua valendo, porque a questão e o gabarito são os mesmos. Os pares em
dúvida vão para uma página de revisão lado a lado (antiga | nova | PDF), igual à página de alertas.

## Formato na plataforma

A plataforma hoje mostra o enunciado como texto simples: separa parágrafos, não mostra fórmula (LaTeX), tabela
nem negrito, e põe todas as imagens depois do enunciado. As questões novas precisam disso para ficarem fiéis.

* **Recomendado:** atualizar o `QuestaoCard` do `omapa` (Lovable) para mostrar markdown simples, tabelas,
  fórmulas (KaTeX) e a imagem no lugar marcado (`{{img:k}}`). As questões antigas continuam aparecendo igual.
* Alternativa pior: converter o texto novo para texto simples (fórmulas viram `a/b`, tabelas viram linhas).

Campos das questões novas no formato do banco: `id`, `exam` (ENEM, SSA, FUVEST, UNICAMP…), `prova` (arquivo de
origem), `ano`, `number`, `statement`, `alternativas`, `gabarito`, `tem_imagem`, `imagens` (arquivos em
`imagens/`, nome `<id>_<k>.png`, reduzidos para web). Comentário, flashcards e tema ficam vazios até as próximas
fases (classificação e comentários). A plataforma precisa aceitar questão sem comentário (mostrar só o gabarito).

Primeira leva: só objetivas prontas (as discursivas precisam de outra tela).

## Etapas

1. **Mapa de repetidas** (código): para cada questão antiga, o par no banco novo e a decisão automática.
   Saída: `unificacao/pares.json` + resumo.
2. **Revisão humana dos pares em dúvida** (página de revisão, marcação salva).
3. **Conversor** (código): banco novo → formato da plataforma, com ids novos e imagens para web.
4. **Plataforma** (Lovable): mostrar fórmula, tabela e imagem no lugar; questão sem comentário.
5. **Teste**: gerar as partes novas num ramo, conferir contagens e uma amostra na tela, sem mexer nas partes antigas.
6. **Publicar**: juntar ao ramo padrão do `Banco-de-questoes`; a sincronização cria as questões novas.
7. Depois: classificação (a plataforma já tem a taxonomia em `areas → materias → assuntos → subassuntos`) e
   comentários das questões novas.

## Plano de trabalho (combinado em 30/09/2026)

Decisões do Matheus:
* Questão repetida: fica a **melhor extração** (antiga ou nova); o **gabarito comentado antigo sempre fica**.
* Questões novas entram só com o gabarito; o comentário vem depois.
* A classificação usa o sistema que já existe na plataforma (áreas → matérias → assuntos → subassuntos).
* Antes de executar, o plano é fechado com as informações que faltam.

### Fase 0 — Informações do Matheus (Lovable/Supabase)
Exportar em CSV (Lovable → Cloud → Database → tabela → Export): `areas`, `materias`, `assuntos`, `subassuntos`,
`depara_texto_livre`, `questoes` e as tabelas de relatos de erro e de respostas dos alunos; prints da tela do banco
(aluno e mentor); o que incomoda hoje e o que falta; vestibulares prioritários.

### Fase 1 — Diagnóstico (Claude, sem mexer em nada)
Ler os CSVs: quantas questões estão publicadas e classificadas, como a taxonomia está organizada, quais questões
antigas os alunos já responderam ou relataram com erro (essas nunca mudam de id).

### Fase 2 — Unificação
Mapa de repetidas com decisão automática; página de revisão lado a lado para os pares em dúvida.

### Fase 3 — Conversão
Banco novo no formato da plataforma, ids a partir de 100.001, imagens para web.

### Fase 4 — Plataforma (prompts para o Lovable, um por vez, pequenos)
Texto rico (fórmula, tabela, negrito, imagem no lugar), questão sem comentário, filtros por vestibular/ano/prova,
imagens no Storage do Supabase se o GitHub ficar lento, e o que vier da Fase 0.

### Fase 5 — Classificação
Na taxonomia da plataforma: área e matéria pelo código (área da prova, ordem das questões), assunto e subassunto
pelo Claude, em lotes, usando as 5 mil questões antigas já classificadas como exemplo.

### Fase 6 — Carga
Teste num ramo, conferência de contagens e amostra na tela, publicação.

### Depois
Comentários das questões novas; provas danificadas (`docs/lotes/pdfs_para_conseguir.md`); discursivas.
