# Mutirão enem2000a2008 — fórmula (2 questões)

Uma imagem pequena no meio do texto pode ser fórmula ou símbolo. Se for, troque {{img:N}} pela fórmula em KaTeX e liste N em remove_imagens.

Formato da resposta (um objeto JSON; junte ao `ferramentas_nuvem/fabrica/correcoes/enem2000a2008.json`):
```json
{"<origem>": {"motivo": "o que foi lido no recorte", "statement_sub": [["regex que acha o trecho", "texto certo"]],
              "alt_sub": {"B": ["regex", "texto"]}, "alternativas": {"C": "texto inteiro"}, "remove_imagens": [2]},
 "_fora": {"<origem>": "motivo (só se for impossível ter certeza)"},
 "_casa": {"<origem>": [<id no banco>, "motivo"]}}
```
Regras: cópia fiel do recorte, nada inventado. Na dúvida, `_fora` com o motivo. Nunca mude o gabarito.

## P7521-Q012
- recorte: `_banco/pendentes/enem2000a2008/P7521-Q012.png`
- motivos: imagem 2 é pequena (pode ser fórmula ou símbolo no meio do texto) — conferir a posição

```
A queima de cana aumenta a concentração de dióxido de carbono e de material particulado na atmosfera, causa alteração do clima e contribui para o aumento de doenças respiratórias. A tabela abaixo apresenta números relativos a pacientes internados em um hospital no período da queima da cana.

{{img:1}}

Escolhendo-se aleatoriamente um paciente internado nesse hospital por problemas respiratórios causados pelas queimadas, a probabilidade de que ele seja uma criança é igual a
  (A) 0,26, o que sugere a necessidade de implementação de medidas que reforcem a atenção ao idoso internado com problemas respiratórios.
  (B) 0,50, o que comprova ser de grau médio a gravidade dos problemas respiratórios que atingem a população nas regiões das queimadas.
  (C) 0,63, o que mostra que nenhum aspecto relativo à saúde infantil pode ser negligenciado.
  (D) 0,67, o que indica a necessidade de campanhas de conscientização que objetivem a eliminação das queimadas.
  (E) 0,75, o que sugere a necessidade de que, em áreas atingidas pelos efeitos das queimadas, o atendimento hospitalar no setor de pediatria seja reforçado.

{{img:2}}
```

## P7521-Q024
- recorte: `_banco/pendentes/enem2000a2008/P7521-Q024.png`
- motivos: imagem 1 é pequena (pode ser fórmula ou símbolo no meio do texto) — conferir a posição

```
**Texto para as questões 23 e 24**

O *Aedes aegypti* é vetor transmissor da dengue. Uma pesquisa feita em São Luís – MA, de 2000 a 2002, mapeou os tipos de reservatório onde esse mosquito era encontrado. A tabela abaixo mostra parte dos dados coletados nessa pesquisa.

{{img:1}}

{{fonte:1}}

Se mantido o percentual de redução da população total de *A. aegypti* observada de 2001 para 2002, teria sido encontrado, em 2003, um número total de mosquitos
  (A) menor que 5.000.
  (B) maior que 5.000 e menor que 10.000.
  (C) maior que 10.000 e menor que 15.000.
  (D) maior que 15.000 e menor que 20.000.
  (E) maior que 20.000.

{{img:2}}
```
