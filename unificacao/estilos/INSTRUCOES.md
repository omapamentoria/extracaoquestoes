# Estilos de questão (Fase 5c)

O banco já está classificado até o subassunto. Agora cada subassunto ganha um nível a mais, o **estilo de questão**.
Com ele, a plataforma vai poder dizer ao aluno, por exemplo: "em Juros, você erra mais as questões que pedem a taxa".

## O que é um estilo

É **o que a questão pede e o passo que decide o acerto**. Não é o tema do texto de apoio. Duas questões do mesmo
estilo exigem o mesmo raciocínio, mesmo que o contexto seja diferente.

Exemplos em Juros compostos: "pede o montante", "pede a taxa", "pede o tempo (logaritmo)", "compara duas aplicações",
"lê o gráfico de crescimento".

## Regras da lista de estilos

* **De 2 a 8 estilos** por subassunto. Subassunto muito pequeno, com menos de 15 questões, pode ter 1 ou 2.
* Estilos que **não se sobrepõem** e que, juntos, cobrem quase todas as questões. O que sobrar vai para um estilo
  "Outros", usado só se necessário e com no máximo 10% das questões.
* Cada estilo precisa ter, se possível, **pelo menos 5 questões**. Se tiver menos, junte com outro estilo.
* **Nome** curto, que o aluno entenda (até ~45 caracteres), começando por verbo quando der: "Calcula a taxa de
  juros", "Interpreta a ironia do texto", "Relaciona massa e volume de gás".
* **Descrição** de uma linha, para quem for classificar: o que caracteriza o estilo e como diferenciá-lo dos outros.
* O estilo não pode depender do vestibular nem do ano.
* Questões de prova estrangeira continuam com nomes em português.

## Formato do arquivo de lista

`unificacao/estilos/listas/<SUBASSUNTO>.json`:

    {"subassunto": "A002-05",
     "estilos": [{"codigo": "A002-05-E1", "nome": "Calcula o montante", "descricao": "..."}, ...],
     "atribuicao": [{"id": 100123, "estilo": "A002-05-E1"}, ...]}

* Os códigos são `<SUBASSUNTO>-E1`, `-E2`… na ordem de importância (o mais comum primeiro). Se houver o estilo
  "Outros", ele é sempre `<SUBASSUNTO>-E9`.
* Em `atribuicao` vai **cada questão do arquivo de questões**, uma vez só, com um estilo principal.
