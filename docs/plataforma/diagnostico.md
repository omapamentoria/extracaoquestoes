# Diagnóstico da plataforma (30/09/2026)

Fonte: consulta `docs/consulta_mapa_banco.sql` (resultado em `mapa_banco_2026-09-30.json`), código do `omapa` e prints.

## Números
* 5.288 questões publicadas (ENEM 4.099, SSA 830, FPS 359); 611 com imagem.
* Classificação: 5 áreas, 15 matérias, 116 assuntos, 379 subassuntos (de 1 a 10 por assunto; todos ativos).
  `assuntos_prova` diz em quais provas cada assunto cai (enem, ssa1, ssa2, ssa3, insper, fps).
* Das 5.288: 5.216 com matéria, **4.213 com assunto, só 1.591 com subassunto**. Nota de revisão: 1.755 nota 5,
  601 nota 4, 2.932 sem nota.
* Uso: 9 alunos com acesso, 5 responderam, 33 respostas, 41 listas, 156 questões em listas, 0 relatos.
  Risco de mexer no banco é baixo; as 156 questões em listas não mudam de id.

## O que está errado hoje
1. **"Somente questões com imagem" vem marcado.** A lista só sorteia entre as 611 com imagem (12% do banco).
2. **Questão sem assunto nunca aparece** (a busca exige `assunto_codigo`): 1.075 questões invisíveis.
3. **Não dá para escolher subassunto** na tela, embora a função aceite.
4. **Origem da questão não aparece** (só "FPS"); falta vestibular, ano e número.
5. **Extração antiga com defeitos visíveis**: número da questão no enunciado ("33. Se as rodas…"), recorte da página
   inteira como imagem (com pedaço da questão seguinte), texto sem parágrafos. Resolve-se trocando pela extração nova.
6. A tela não mostra fórmula, tabela, negrito nem imagem no meio do texto.

## O que está bom e fica
Criar lista por conteúdo, listas salvas, riscar alternativa, comentário por alternativa, passos do raciocínio,
alternativa correta / incorretas / quadro-resumo, "leve para a prova", flashcards, reportar erro.

## Estilo de questão e a classificação atual
Alguns exemplos do Matheus já são subassuntos (Química → Reações e cálculos químicos → **Pureza e rendimento**).
O estilo fica um nível abaixo do subassunto: em "Juros e matemática financeira", por exemplo, "pede a taxa",
"pede o montante", "pede o tempo"; em "Pureza e rendimento", "pede a pureza", "pede o rendimento", "pede a massa
com os dois".
