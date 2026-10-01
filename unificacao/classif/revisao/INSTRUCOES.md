# Revisão das questões de confiança baixa

Na primeira passada, estas questões ficaram com confiança baixa. Agora você tem o enunciado mais completo, as
alternativas inteiras, o gabarito e a primeira tentativa. Sua tarefa é **decidir o subassunto final** de cada
questão, com cuidado.

1. Leia a taxonomia inteira em `unificacao/classif/taxonomia.txt`.
2. Para cada questão do lote `unificacao/classif/revisao/lotes/rev_NN.json`:
   - descubra **o que a questão cobra para ser resolvida**: qual conhecimento leva à alternativa do gabarito.
     Não classifique pelo tema do texto de apoio;
   - procure na taxonomia o subassunto que melhor descreve esse conhecimento. Compare com a primeira tentativa:
     mantenha-a se for a melhor, troque se houver outra melhor;
   - questão de inglês ou espanhol vai para a matéria da língua. Questão interdisciplinar vai para a matéria do
     raciocínio principal;
   - escolha sempre um código que exista na taxonomia, mesmo quando nada encaixar perfeitamente. Nesse caso,
     escolha o mais próximo.
3. Grave `unificacao/classif/revisao/respostas/rev_NN.json`: um array JSON, na mesma ordem do lote, com um objeto
   por questão:

       {"id": 123, "sub": "A064-01", "conf": "alta|media|baixa", "motivo": "frase curta: o que a questão cobra"}

   Use `conf` para dizer o quanto o subassunto escolhido descreve bem a questão.
