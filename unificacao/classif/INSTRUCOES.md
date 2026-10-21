# Classificação das questões (matéria > assunto > subassunto)

Você classifica questões de vestibular e ENEM na taxonomia da plataforma MAPA.

1. Leia a taxonomia inteira em `unificacao/classif/taxonomia.txt`. A hierarquia é área > matéria > assunto > subassunto.
2. Leia o lote pedido, `unificacao/classif/lotes/lote_NNN.json`. Cada questão traz:
   - `id`;
   - `vest` e `ano`;
   - `area`: a área impressa na prova. É uma dica, e pode vir `null`;
   - `texto`: o enunciado resumido, com "[…]" onde houve corte, seguido de "||" e das alternativas.
3. Para CADA questão, escolha **um** subassunto: o código exato da taxonomia, por exemplo `A064-01`.

Como escolher:
- Classifique pelo **conhecimento que a questão cobra para ser resolvida**, e não pelo assunto do texto de apoio.
  Por exemplo, um texto sobre desmatamento com uma pergunta sobre a função sintática de um termo é Português.
- Questão de inglês ou espanhol (texto na língua estrangeira) vai para a matéria Inglês ou Espanhol, no subassunto
  que melhor descreve o que se pede (compreensão, vocabulário, gramática…).
- Questão interdisciplinar: escolha a matéria do raciocínio principal, aquele sem o qual não se chega à resposta.
- `area` costuma estar certa. Só escolha outra área quando o conteúdo for claramente de outra.
- Nunca invente código. Se nada encaixar bem, escolha o subassunto mais próximo e marque `"conf": "baixa"`.
- Use `alta` quando não há dúvida, `media` quando dois subassuntos disputam, e `baixa` quando nenhum encaixa bem.

Resposta: grave `unificacao/classif/respostas/lote_NNN.json` (mesmo número do lote). O arquivo é um array JSON com um
objeto por questão, na mesma ordem do lote, e nada mais:

    [{"id": 120907, "sub": "A064-01", "conf": "alta"}, ...]

Antes de gravar, confira: o número de objetos é igual ao do lote, os ids estão na mesma ordem e todo `sub` existe na
taxonomia.
