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

## Plano de trabalho completo (30/09/2026)

Decisões do Matheus:
* Questão repetida: fica a **melhor extração** (antiga ou nova); o **gabarito comentado antigo sempre fica**.
* Questões novas entram só com o gabarito; o comentário vem depois.
* A classificação usa o sistema da plataforma (área → matéria → assunto → subassunto) e ganha um nível novo:
  o **estilo de questão**, dentro de cada subassunto.
* O objetivo final: a plataforma dizer ao aluno não só o assunto que ele mais erra, mas **o estilo de questão**
  que ele mais erra dentro do assunto.
* Nada é executado antes do plano fechado.

### Classificação em 5 níveis

    Área → Matéria → Assunto → Subassunto → Estilo de questão
    Natureza → Química → Estequiometria → Cálculo estequiométrico → "pede a pureza do reagente"
    Exatas → Matemática → Matemática financeira → Juros compostos → "pede a taxa mensal"

**O que é um estilo.** É o que a questão pede e o passo que decide o acerto, não o tema do texto. Duas questões do
mesmo estilo exigem o mesmo raciocínio, mesmo com contextos diferentes. Exemplos de juros compostos: "pede o
montante", "pede a taxa", "pede o tempo (logaritmo)", "compara duas aplicações", "lê o gráfico de crescimento".

**Regras de uma boa lista de estilos** (para o diagnóstico fazer sentido):
* de 2 a 8 estilos por subassunto; cada questão tem **um estilo principal**;
* estilos que não se sobrepõem, cobrindo quase todas as questões do subassunto (o resto vai para "outros");
* cada estilo com pelo menos 5 questões no banco (senão junta com outro);
* nome curto que o aluno entende ("pede a taxa mensal") e uma descrição de uma linha para o classificador.

**Como a lista nasce** (decisão do Matheus, 30/09): primeiro todas as questões são classificadas até o
subassunto. Depois, para cada subassunto, o Claude lê as questões dele, identifica os estilos sozinho e classifica
cada questão num deles. O Matheus não participa da criação dos estilos (são muitos subassuntos); recebe só um
resumo por matéria e pode pedir ajuste onde quiser. Piloto em 3 subassuntos só para calibrar o tamanho dos estilos.

**Na plataforma.** Tabela nova `estilos_questao` (código, subassunto, nome, descrição) e coluna `estilo_codigo` em
`questoes`. O diagnóstico do aluno cruza `question_attempts` (acertos e erros) com o estilo: "em Juros compostos,
você erra mais as questões que pedem a taxa". Os erros de simulado (`erros_simulado_questoes`) podem ganhar o mesmo
campo depois.

### Fases

| Fase | Quem | O que |
|---|---|---|
| 0. Informações | Matheus | Resultado da consulta `docs/consulta_mapa_banco.sql` (tudo de uma vez), prints e respostas |
| 1. Diagnóstico | Claude | Ler os CSVs sem mexer em nada: o que está publicado, a taxonomia, o que os alunos já usam |
| 2. Unificação | Claude + Matheus | Repetidas: fica a melhor extração, comentário antigo sempre; pares em dúvida numa página de revisão |
| 3. Conversão | Claude | Banco novo no formato da plataforma, ids a partir de 100.001, imagens para web |
| 4. Plataforma | Claude escreve, Matheus cola no Lovable | Prompts pequenos, um de cada vez: texto rico (fórmula, tabela, imagem no lugar), questão sem comentário, filtros por vestibular/ano/prova, tabela de estilos, diagnóstico por estilo |
| 5a. Taxonomia | Claude + Matheus | Conferir se área → subassunto cobre o banco novo (FUVEST, UNICAMP etc.); propor o que falta |
| 5b. Classificação até subassunto | Claude | Área e matéria pelo código; assunto e subassunto em lotes, com as 5 mil antigas como exemplo |
| 5c. Estilos | Claude | Depois do 5b: estilos criados por subassunto a partir das questões dele e cada questão classificada; resumo por matéria para o Matheus |
| 6. Carga | Claude + Matheus | Teste num ramo, conferência, publicação |
| Depois | | Comentários das novas; provas danificadas; discursivas |

A classificação (5b e 5c) é a parte mais cara em uso do Claude: cerca de 41 mil questões, em várias sessões.
