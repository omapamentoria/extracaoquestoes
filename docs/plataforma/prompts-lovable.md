# Prompts para o Lovable (colar um por vez, na ordem; testar antes de passar ao próximo)

## Prompt 1 — Correções do Banco de Questões (pode colar já)

> No Banco de Questões (página `BancoQuestoes.tsx`, componente `QuestaoCard.tsx` e função `question-bank`):
>
> 1. A opção "Somente questões com imagem" deve vir **desmarcada** por padrão.
> 2. Acrescente o filtro de **Subassunto** depois de "Assunto" (lista os subassuntos do assunto escolhido, tabela
>    `subassuntos`); a função `question-bank` já aceita `subassuntoCodigo`.
> 3. Permita criar lista só com a **Área** escolhida (hoje exige matéria ou assunto).
> 4. Na criação da lista, não exija `assunto_codigo` preenchido quando o filtro for só área ou matéria: questões
>    ainda sem assunto também podem entrar.
> 5. No topo de cada questão, mostre a origem: vestibular (`prova`), ano (`ano`) e número (`numero`), por exemplo
>    "FPS 2019 · questão 33", ao lado do chip do tema.
>
> Não mude mais nada.

## Prompt 2 — Texto rico da questão e campos novos (Fase 4)

> Vamos preparar o Banco de Questões para receber questões com formatação. Não mude o que já funciona.
>
> **1. Migração** em `questoes`: `fontes jsonb not null default '[]'`, `apos_alternativas text`, `vestibular text`,
> `edicao text`, `dia text`, `formato text default 'objetiva'`, `origem_texto text`.
>
> **2. `question-bank-sync`**: ler também do JSON os campos `fontes`, `apos_alternativas`, `vestibular`, `edicao`, `dia`,
> `formato` e `origem_texto` e gravar nas colunas novas. Se o JSON trouxer `area_codigo`, `materia_codigo`,
> `assunto_codigo` ou `subassunto_codigo`, usar esses códigos direto (sem a busca por nome). Se o `gabarito` vier
> como `"anulada"`, gravar `status = 'anulada'` (fora das listas).
>
> **3. `QuestaoCard.tsx`**: mostrar enunciado, alternativas e `apos_alternativas` com formatação:
> * parágrafos separados por linha em branco; `**negrito**`, `*itálico*`, `<sup>`, `<sub>`, `<u>`, `<br>`;
> * tabelas em markdown (`| a | b |`), com rolagem horizontal no celular;
> * fórmulas entre `\(` e `\)` com KaTeX (instalar `katex`);
> * `{{img:N}}` = a N-ésima imagem da lista `imagens`, mostrada **naquele ponto do texto**; imagem que já apareceu
>   no texto não se repete no fim; uma alternativa pode ser só `{{img:N}}` (a alternativa é a imagem);
> * `{{fonte:N}}` = o N-ésimo item de `fontes`, em texto pequeno e cinza (crédito do texto ou da imagem);
> * as imagens novas são `.webp` e ficam na mesma pasta `imagens/` (a função `question-bank-image` já aceita).
> Questões antigas (sem esses marcadores) continuam aparecendo exatamente como hoje.
>
> **4.** No topo da questão, a origem passa a usar `vestibular`, `ano`, `edicao` e `dia` quando existirem
> (ex.: "ENEM 2019 · 2º dia · questão 135").

## Prompt 3 — Questão sem comentário e questão anulada (Fase 4)

> 1. Questão sem comentário (`explicacao_correta_texto` vazio e `passos_raciocinio` vazio): depois de responder,
>    mostrar só o gabarito ("Gabarito: C") e a frase "Comentário em produção". Esconder as abas vazias e os flashcards.
> 2. No filtro de criar lista, opção "Só questões comentadas" (desmarcada por padrão).
> 3. Questões com `status = 'anulada'` nunca entram em listas.

## Prompt 4 — Imagens no Storage (Fase 4, antes da carga)

> As imagens das questões passam a ficar no bucket público `questoes-imagens` do Storage. Na `question-bank-sync`,
> para cada imagem nova ou alterada do repositório (`imagens/`), copiar para o bucket com o mesmo nome. No
> `QuestaoCard.tsx`, carregar a imagem do bucket e, se não existir, cair na função `question-bank-image` (como hoje).

## Prompt 5 — Estilo de questão e diagnóstico (Fase 5c, depois da classificação)

> Tabela `estilos_questao` (`codigo text primary key`, `subassunto_codigo text references subassuntos`, `nome text`,
> `descricao text`, `ordem int`), coluna `estilo_codigo` em `questoes`, `question_attempts` e
> `erros_simulado_questoes`. A `question-bank-sync` lê `estilo_codigo` do JSON e os estilos de
> `final/estilos.json`. Em "Criar lista", filtro opcional de estilo depois de subassunto. Nova seção "Onde eu erro"
> para o aluno: por assunto, a taxa de erro; ao abrir o assunto, os subassuntos e, dentro de cada um, os estilos com
> mais erros (mínimo de 3 respostas para mostrar), com botão "Treinar este estilo" que cria a lista.
