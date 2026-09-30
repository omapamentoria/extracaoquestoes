# O que o Matheus manda do Lovable (Fase 0)

## Como exportar uma tabela em CSV
No Lovable, abra o projeto → **Cloud** → **Database** → **Tables** → clique na tabela → botão de exportar/baixar CSV.
Se não achar o botão, peça no chat do Lovable: *"Exporte a tabela `NOME` inteira em CSV para eu baixar."*
Coloque os arquivos numa pasta do Google Drive compartilhada por link (ou mande aqui).

## Tabelas (nesta ordem de importância)

| # | Tabela | Para quê |
|---|---|---|
| 1 | `areas` | classificação |
| 2 | `materias` | classificação |
| 3 | `assuntos` | classificação |
| 4 | `subassuntos` | classificação |
| 5 | `assuntos_prova` | quanto cada assunto cai em cada prova (se existir conteúdo) |
| 6 | `depara_texto_livre` | como os temas antigos viraram códigos |
| 7 | `questoes` | o que está publicado e classificado hoje |
| 8 | `question_attempts` | respostas dos alunos (base do diagnóstico por estilo) |
| 9 | `question_reports` | erros que os alunos reportaram nas questões |
| 10 | `question_sessions` e `question_session_items` | listas já montadas (questões usadas não mudam de id) |
| 11 | `erros_simulado_questoes` | como os erros de simulado são classificados hoje |

Se a 7, 8 ou 10 for grande demais para exportar, peça ao Lovable um resumo: *"Quantas linhas tem cada uma das
tabelas questoes, question_attempts, question_reports, question_sessions e question_session_items, e quantos
alunos diferentes aparecem em question_attempts?"*

## Prints
1. Banco de Questões do aluno: tela de filtros, uma questão aberta, o comentário aberto, o resultado da lista.
2. Tela do mentor do banco (acessos, relatos, sincronização).
3. Onde o aluno vê hoje os assuntos que mais erra (caderno de erros / desempenho), se existir.

## Perguntas
1. O que mais incomoda hoje no banco de questões?
2. O que falta? (filtro por vestibular/ano/prova, simulado com tempo, estatística por assunto, refazer as erradas…)
3. Quais vestibulares os alunos mais fazem? (ordem de classificação e de comentários)
4. Os alunos já usam o banco hoje? Quantos, mais ou menos?
5. Posso sugerir guardar as imagens no Storage do Supabase em vez do GitHub?
6. Estilos de questão: tem subassuntos que você já quer ver no piloto? Tem exemplos de estilos que você usa nas
   mentorias e quer ver no banco?
