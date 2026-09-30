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

## Prompt 2 — Texto rico da questão (colar na Fase 4)

> No `QuestaoCard.tsx`, mostre o enunciado, as alternativas e o campo novo `apos_alternativas` com formatação:
> * parágrafos separados por linha em branco; `**negrito**`, `*itálico*`, `<sup>`, `<sub>`, `<u>`, `<br>`;
> * tabelas em markdown (`| a | b |`);
> * fórmulas entre `\(` e `\)` com KaTeX (instalar `katex`);
> * `{{img:N}}` no texto = a N-ésima imagem de `imagens`, mostrada **naquele ponto**; imagem citada no texto não
>   se repete no fim; alternativa pode ter `{{img:N}}` (a alternativa é a imagem);
> * `{{fonte:N}}` = o N-ésimo item do campo novo `fontes` (texto pequeno e cinza, como crédito).
> Questões antigas (sem esses marcadores) continuam aparecendo exatamente como hoje.
> Migração: colunas `fontes jsonb default '[]'`, `apos_alternativas text`, `vestibular text`, `edicao text`,
> `formato text default 'objetiva'` em `questoes`; a função `question-bank-sync` passa a ler esses campos do JSON
> (`fontes`, `apos_alternativas`, `vestibular`, `edicao`, `formato`) e, quando o JSON trouxer `area_codigo`,
> `materia_codigo`, `assunto_codigo`, `subassunto_codigo`, usa esses códigos direto (sem a busca por nome).

## Prompt 3 — Questão sem comentário (Fase 4)

> Questões sem comentário (`explicacao_correta_texto` vazio e `passos_raciocinio` vazio): depois de responder,
> mostrar só o gabarito ("Gabarito: C") e a frase "Comentário em produção". Esconder as abas vazias e os flashcards.
> No filtro, opção "Só questões comentadas" (desmarcada por padrão).

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
