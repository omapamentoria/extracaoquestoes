# Mutirão enem2000a2008 — figura (25 questões)

A figura pode estar cortada, ter texto dentro ou rótulo solto. Confira com o recorte; se o texto da figura já está no enunciado, nada a fazer.

Formato da resposta (um objeto JSON; junte ao `ferramentas_nuvem/fabrica/correcoes/enem2000a2008.json`):
```json
{"<origem>": {"motivo": "o que foi lido no recorte", "statement_sub": [["regex que acha o trecho", "texto certo"]],
              "alt_sub": {"B": ["regex", "texto"]}, "alternativas": {"C": "texto inteiro"}, "remove_imagens": [2]},
 "_fora": {"<origem>": "motivo (só se for impossível ter certeza)"},
 "_casa": {"<origem>": [<id no banco>, "motivo"]}}
```
Regras: cópia fiel do recorte, nada inventado. Na dúvida, `_fora` com o motivo. Nunca mude o gabarito.

## P7507-Q009
- recorte: `_banco/pendentes/enem2000a2008/P7507-Q009.png`
- motivos: texto curto solto junto da imagem (“**1**  
**4**”): pode ser rótulo da figura — conferir

```
A tabela abaixo resume alguns dados importantes sobre os satélites de Júpiter.

{{img:1}}

Ao observar os satélites de Júpiter pela primeira vez, Galileu Galilei fez diversas anotações e tirou importantes conclusões sobre a estrutura de nosso universo. A figura abaixo reproduz uma anotação de Galileu referente a Júpiter e seus satélites.

**1**  
**4**

{{img:2}}

De acordo com essa representação e com os dados da tabela, os pontos indicados por 1, 2, 3 e 4 correspondem, respectivamente, a:
  (A) Io, Europa, Ganimedes e Calisto.
  (B) Ganimedes, Io, Europa e Calisto.
  (C) Europa, Calisto, Ganimedes e Io.
  (D) Calisto, Ganimedes, Io e Europa.
  (E) Calisto, Io, Europa e Ganimedes.
```

## P7507-Q026
- recorte: `_banco/pendentes/enem2000a2008/P7507-Q026.png`
- motivos: texto curto solto junto da imagem (“7”): pode ser rótulo da figura — conferir

```
A tabela abaixo apresenta**a l g u m a s** das principais causas de mortes no Brasil, distribuídas por região.

{{img:1}}

7

4 Fonte: Ministério da Saúde, 1996

São conhecidas ainda as seguintes informações sobre as causas de óbitos:

**-** A dificuldade na obtenção de informações, a falta de notificação e o acesso

precário aos serviços de saúde são fatores relevantes na contabilização dos óbitos por causas mal definidas.

**-** O aumento da esperança de vida faz com que haja cada vez mais pessoas

com maiores chances de desenvolver algum tipo de câncer.

**-** As mortes por doenças do aparelho respiratório estão estreitamente

associadas à poluição nos grandes centros urbanos.

**-** Os acidentes de trânsito e os assassinatos representam a quase totalidade

das mortes por causas externas.

**-** A região Norte é a única que apresenta todas as taxas por 10.000

habitantes abaixo da taxa média brasileira.

Levando em consideração essas informações e o panorama social, econômico e ambiental do Brasil, pode-se concluir que as regiões K, X, W, Y e Z da tabela indicam, respectivamente, as regiões:
  (A) Sul, Norte, Nordeste, Sudeste e Centro-Oeste.
  (B) Centro-Oeste, Sudeste, Norte, Nordeste e Sul.
  (C) Centro-Oeste, Nordeste, Norte, Sul e Sudeste.
  (D) Norte, Nordeste, Sul, Centro-Oeste e Sudeste.
  (E) Norte, Sudeste, Centro-Oeste, Nordeste e Sul.
```

## P7507-Q050
- recorte: `_banco/pendentes/enem2000a2008/P7507-Q050.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto; 1 alternativas encontradas (esperado 5); alternativas fora do padrão A–E

```
O esquema ilustra o processo de obtenção do álcool etílico a partir da cana-de-açúcar.

{{img:1}}

quantidade de cana-de-açúcar, em toneladas, que teve de ser colhida para esse fim foi aproximadamente
  (A) 1,7 x 108. (B) 1,2 x 109. (C) 1,7 x 109. (D) 1,2 x 1010. (E) 7,0 x 1010.
```

## P7509-Q028
- recorte: `_banco/pendentes/enem2000a2008/P7509-Q028.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
{{img:1}}

**O aspecto** <u>**biológico,**</u> **ressaltado a partir da leitura do gráfico, que pode ser considerado o melhor argumento para que o produtor não retome o uso do veneno é:**
  (A) A densidade populacional das larvas e dos parasitas não é afetada pelo uso do veneno.**
  (B) A população de larvas não consegue se estabilizar durante o uso do veneno.**
  (C) As populações mudam o tipo de interação estabelecida ao longo do tempo.**
  (D) As populações associadas mantêm um comportamento estável durante todo o período.**
  (E) Os efeitos das interações negativas diminuem ao longo do tempo, estabilizando as populações.**
```

## P7509-Q059
- recorte: `_banco/pendentes/enem2000a2008/P7509-Q059.png`
- motivos: figura na pág. 12 depois da alternativa E foi descartada (não faz parte da questão) — conferir; há texto depois das alternativas (“Adaptado Atlas Nacional do Brasil, IBGE, 1992/ htt”): conferir se é desta questão; texto curto solto junto da imagem (“Agricultura”): pode ser rótulo da figura — conferir

```
**O gráfico mostra a porcentagem da força de trabalho brasileira em 40 anos, com relação aos setores agrícola, de serviços e industrial/mineral.**

{{img:1}}

Agricultura

Serviços Indústria/mineração

**A leitura do gráfico permite constatar que:**
  (A) Em 40 anos, o Brasil deixou de ser essencialmente agrícola para se tornar uma sociedade quase que exclusivamente industrial.**
  (B) A variação da força de trabalho agrícola foi mais acentuada no período de 1940 a 1960.**
  (C) Por volta de 1970, a força de trabalho agrícola tornou-se equivalente à industrial e de mineração.**
  (D) Em 1980, metade dos trabalhadores brasileiros constituía a força de trabalho do setor agrícola.**
  (E) De 1960 a 1980, foi equivalente o crescimento percentual de trabalhadores nos setores industrial/mineral e de serviços. 60 A Mata Atlântica, que originalmente se estendia por todo o litoral brasileiro, do Ceará ao Rio Grande do Sul, ostenta hoje o triste título de uma das florestas mais devastadas d
```

## P7511-Q030
- recorte: `_banco/pendentes/enem2000a2008/P7511-Q030.png`
- motivos: figura na pág. 14 depois da alternativa E foi descartada (não faz parte da questão) — conferir

```
*Só falta o Senado aprovar o projeto de lei [sobre o uso de termos estrangeiros no Brasil] para que palavras como shopping* *center , delivery e drive-through sejam proibidas em nomes de estabelecimentos e marcas. Engajado nessa valorosa luta* *contra o inimigo ianque, que quer fazer área de livre comércio com nosso inculto e belo idioma, venho sugerir algumas outras* *medidas que serão de extrema importância para a preservação da soberania nacional, a saber:*

*........*

! *Nenhum cidadão carioca ou gaúcho poderá dizer “Tu vai” em espaços públicos do território nacional;*  
! *Nenhum cidadão paulista poderá dizer “Eu lhe amo” e retirar ou acrescentar o plural em sentenças como “Me vê um chopps*

*e dois pastel”;*  
*..........*

! *Nenhum dono de borracharia poderá escrever cartaz com a palavra “borraxaria” e nenhum dono de banca de jornal*

*anunciará “Vende-se cigarros”;*  
*..........*

! *Nenhum livro de gramática obrigará os alunos a utilizar colocações pronominais como “casar-me-ei” ou “ver-se-ão”.*

{{fonte:1}}

{{fonte:2}}

No texto acima, o autor
  (A) mostra-se favorável ao teor da proposta por entender que a língua portuguesa deve ser protegida contra deturpações de uso.
  (B) ironiza o projeto de lei ao sugerir medidas que inibam determinados usos regionais e socioculturais da língua.
  (C) denuncia o desconhecimento de regras elementares de concordância verbal e nominal pelo falante brasileiro.
  (D) revela-se preconceituoso em relação a certos registros lingüísticos ao propor medidas que os controlem.
  (E) defende o ensino rigoroso da gramática para que todos aprendam a empregar corretamente os pronomes. A corvina é um peixe carnívoro que se alimenta de crustáceos, moluscos e pequenos peixes que vivem no fundo do mar. É bastante utilizada na alimentação humana, sendo encontrada em toda a costa brasile
```

## P7513-Q033
- recorte: `_banco/pendentes/enem2000a2008/P7513-Q033.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
Visando adotar um sistema de reutilização de água, uma indústria testou cinco sistemas com diferentes fluxos de entrada de água suja e fluxos de saída de água purificada.

{{img:1}}

Supondo que o custo por litro de água purificada seja o mesmo, obtém-se maior eficiência na purificação por meio do sistema
  (A) I
  (B) II
  (C) III
  (D) IV
  (E) V
```

## P7515-Q005
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q005.png`
- motivos: texto curto solto junto da imagem (“**Estratégias:**”): pode ser rótulo da figura — conferir

```
Em 2003, deu-se início às discussões do Plano Amazônia Sustentável, que rebatiza o Arco do Desmatamento, uma extensa faixa que vai de Rondônia ao Maranhão, como Arco do Povoamento Adensado, a fim de reconhecer as demandas da população que vive na região. A Amazônia Ocidental, em contraste, é considerada nesse plano como uma área ainda amplamente preservada, na qual se pretende encontrar alternativas para tirar mais renda da floresta em pé do que por meio do desmatamento. O quadro apresenta as três macrorregiões e três estratégias que constam do Plano.

{{img:1}}

**Estratégias:**

**I.** Pavimentação de rodovias para levar a soja até o rio Amazonas, por onde será escoada.

**II.** Apoio à produção de fármacos, extratos e couros vegetais.

**III.** Orientação para a expansão do plantio de soja, atraindo os produtores para áreas já desmatadas e atualmente abandonadas.

Considerando as características geográficas da Amazônia, aplicam-se às macrorregiões Amazônia Ocidental, Amazônia Central e Arco do Povoamento Adensado, <u>respectivamente,</u> as estratégias
  (A) I, II e III.
  (B) I, III e II.
  (C) III, I e II.
  (D) II, I e III.
  (E) III, II e I.
```

## P7515-Q014
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q014.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto; imagem 1 pode estar cortada (o desenho continua fora do recorte) — conferir; imagem 2 pode estar cortada (o desenho continua fora do recorte) — conferir; imagem 4 pode estar cortada (o desenho continua fora do recorte) — conferir

```
{{img:1}}

{{img:2}}

**DIFERENÇA**  
**(L <sub>I</sub> - L <sub>II</sub>) (cm)**

75  
-25  
55

Ao preencher completamente a tabela, o mestre-de-obras determinou o seguinte perfil para o terreno:
  (A) {{img:3}}
  (B) {{img:4}}
  (C) {{img:5}}
  (D) {{img:6}}
  (E) {{img:7}}
```

## P7515-Q018
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q018.png`
- motivos: imagem 1 pode estar cortada (o desenho continua fora do recorte) — conferir

```
{{img:1}}

O poema abaixo pertence à poesia concreta brasileira. O termo latino de seu título significa “epitalâmio”, poema ou canto em homenagem aos que se casam.

**EPITHALAMIUM – II**

***he = ele***

***S = serpens***  
***& = e***  
***h = homo***  
***She = ela***  
***e = eva***

(Pedro Xisto)

Considerando que símbolos e sinais são utilizados geralmente para demonstrações objetivas, ao serem incorporados no poema “Epithalamium - II”,
  (A) adquirem novo potencial de significação.
  (B) eliminam a subjetividade do poema.
  (C) opõem-se ao tema principal do poema.
  (D) invertem seu sentido original.
  (E) tornam-se confusos e equivocados.
```

## P7515-Q032
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q032.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
O Índice de Desenvolvimento Humano (IDH) permite avaliar as condições de qualidade de vida e de desenvolvimento de um país, de uma região ou de uma cidade, a partir de seus indicadores de renda, longevidade e educação. Cada indicador varia de 0 (nenhum desenvolvimento) a 1 (desenvolvimento máximo). A tabela apresenta os valores de IDH de três municípios brasileiros, X, Y e Z, medidos nos anos de 1991 e 2000.

{{img:1}}

Mudanças desses indicadores de IDH podem ser obtidas com a implantação de políticas públicas tais como:

I. Expansão dos empregos com melhoria de renda média.  
II. Ações de promoção de saúde e de prevenção de doenças.  
III. Ampliação de escolas de ensino básico e de educação de jovens e adultos.

Os resultados apresentados em 2000 são compatíveis com a implementação bem sucedida em todos <u>esses três municípios,</u> ao longo da década de noventa, das políticas
  (A) I, II e III.
  (B) I e II, apenas.
  (C) I e III, apenas.
  (D) II e III, apenas.
  (E) II, apenas.
```

## P7515-Q038
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q038.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
O crescimento da demanda por energia elétrica no Brasil tem provocado discussões sobre o uso de diferentes processos para sua geração e sobre benefícios e problemas a eles associados. Estão apresentados no quadro alguns argumentos favoráveis (ou positivos, P<sub>1</sub>, P<sub>2</sub> e P<sub>3</sub>) e outros desfavoráveis (ou negativos, N<sub>1</sub>, N<sub>2</sub> e N<sub>3</sub>) relacionados a diferentes opções energéticas.

{{img:1}}

Ao se discutir a opção pela instalação, em uma dada região, de uma <u>usina termoelétrica</u>**,** os argumentos que se aplicam são
  (A) P<sub>1</sub> e N<sub>2</sub>.
  (B) P<sub>1</sub> e N<sub>3</sub>.
  (C) P<sub>2</sub> e N<sub>1</sub>.
  (D) P<sub>2</sub> e N<sub>2</sub>.
  (E) P<sub>3</sub> e N<sub>3</sub>.
```

## P7515-Q048
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q048.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
No verão de 2000 foram realizadas, para análise, duas coletas do lixo deixado pelos freqüentadores em uma praia no litoral brasileiro. O lixo foi pesado, separado e classificado. Os resultados das coletas feitas estão na tabela a seguir.

{{img:1}}

Adaptado de *Ciência Hoje*

Embora fosse grande a venda de bebidas em latas nessa praia, não se encontrou a quantidade esperada dessas embalagens  
no lixo coletado, o que foi atribuído à existência de um bom mercado para a reciclagem de alumínio. Considerada essa hipótese, para reduzir o lixo nessa praia, a iniciativa que mais diretamente atende à variedade de interesses envolvidos, respeitando a  
preservação ambiental, seria
  (A) proibir o consumo de bebidas e de outros alimentos nas praias.
  (B) realizar a coleta de lixo somente no período noturno.
  (C) proibir a comercialização apenas de produtos com embalagem.
  (D) substituir embalagens plásticas por embalagens de vidro.
  (E) incentivar a reciclagem de plásticos, estimulando seu recolhimento.
```

## P7515-Q057
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q057.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
A identificação da estrutura do DNA foi fundamental para compreender seu papel na continuidade da vida. Na década de 1950, um estudo pioneiro determinou a proporção das bases nitrogenadas que compõem moléculas de DNA de várias espécies.

{{img:1}}

A comparação das proporções permitiu concluir que ocorre emparelhamento entre as bases nitrogenadas e que elas formam
  (A) pares de mesmo tipo em todas as espécies, evidenciando a universalidade da estrutura do DNA.
  (B) pares diferentes de acordo com a espécie considerada, o que garante a diversidade da vida.
  (C) pares diferentes em diferentes células de uma espécie, como resultado da diferenciação celular.
  (D) pares específicos apenas nos gametas, pois essas células são responsáveis pela perpetuação das espécies.
  (E) pares específicos somente nas bactérias, pois esses organismos são formados por uma única célula.
```

## P7515-Q060
- recorte: `_banco/pendentes/enem2000a2008/P7515-Q060.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
Na fabricação de qualquer objeto metálico, seja um parafuso, uma panela, uma jóia, um carro ou um foguete, a metalurgia está presente na extração de metais a partir dos minérios correspondentes, na sua transformação e sua moldagem. Muitos dos processos metalúrgicos atuais têm em sua base conhecimentos desenvolvidos há milhares de anos, como mostra o quadro:

{{img:1}}

Podemos observar que a extração e o uso de diferentes metais ocorreram a partir de diferentes épocas. Uma das razões para que a extração e o uso do ferro tenham ocorrido após a do cobre ou estanho é
  (A) a inexistência do uso de fogo que permitisse sua moldagem.
  (B) a necessidade de temperaturas mais elevadas para sua extração e moldagem.
  (C) o desconhecimento de técnicas para a extração de metais a partir de minérios.
  (D) a necessidade do uso do cobre na fabricação do ferro.
  (E) seu emprego na cunhagem de moedas, em substituição ao ouro.
```

## P7517-Q023
- recorte: `_banco/pendentes/enem2000a2008/P7517-Q023.png`
- motivos: texto curto solto junto da imagem (“*Preliminar”): pode ser rótulo da figura — conferir

```
Analise o quadro acerca da distribuição da miséria no mundo, nos anos de 1987 a 1998.

{{img:1}}

*Preliminar

{{fonte:1}}

A leitura dos dados apresentados permite afirmar que, no período considerado,
  (A) no sul da Ásia e na África Subsaariana está, proporcionalmente, a maior concentração da população miserável.
  (B) registra-se um aumento generalizado da população pobre e miserável.
  (C) na África Subsaariana, o percentual de população pobre foi crescente.
  (D) em números absolutos a situação da Europa e da Ásia Central é a melhor dentre todas as regiões consideradas.
  (E) o Oriente Médio e o Norte da África mantiveram o mesmo percentual de população miserável.
```

## P7519-Q008
- recorte: `_banco/pendentes/enem2000a2008/P7519-Q008.png`
- motivos: figura na pág. 5 depois da alternativa E foi descartada (não faz parte da questão) — conferir

```
No romance Vidas Secas, de Graciliano Ramos, o vaqueiro Fabiano encontra-se com o patrão para receber o salário. Eis parte da cena:

Não se conformou: devia haver engano. (...) 1

Com certeza havia um erro no papel do branco. Não 4 se descobriu o erro, e Fabiano perdeu os estribos. Passar a vida inteira assim no toco, entregando o que era dele de mão beijada! Estava direito aquilo? 7 Trabalhar como negro e nunca arranjar carta de alforria?

O patrão zangou-se, repeliu a insolência, 10 achou bom que o vaqueiro fosse procurar serviço noutra fazenda.

Aí Fabiano baixou a pancada e amunhecou. Bem, bem. Não era preciso barulho não.

{{fonte:1}}

No fragmento transcrito, o padrão formal da linguagem convive com marcas de regionalismo e de coloquialismo no vocabulário. Pertence à variedade do padrão formal da linguagem o seguinte trecho:
  (A) “Não se conformou: devia haver engano” (ℓ.1).
  (B) “e Fabiano perdeu os estribos” (ℓ.3).
  (C) “Passar a vida inteira assim no toco” (ℓ.4).
  (D) “entregando o que era dele de mão beijada!” (ℓ.4-5).
  (E) “Aí Fabiano baixou a pancada e amunhecou” (ℓ.11). Para responder às questões 9 e 10, analise o quadro a seguir, que esquematiza a história da Terra.
```

## P7519-Q040
- recorte: `_banco/pendentes/enem2000a2008/P7519-Q040.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
{{img:1}}

América<sub>2</sub> do Sul, com 1,2 milhão  
de km , não é o "mar de água

potáveis. Já no compartimento Norte-Alto  
Uruguai, o sistema encontra-se coberto por rochas vulcânicas, a profundidades que variam de 350 m a 1.200 m. Suas águas são muito antigas, datando da Era Mesozóica, e não são potáveis em grande parte da área, com elevada salinidade, sendo que os altos teores de fluoretos e de sódio podem causar alcalinização do solo.

{{fonte:1}}

Em relação ao aqüífero Guarani, é correto afirmar que
  (A) seus depósitos não participam do ciclo da água.
  (B) águas provenientes de qualquer um de seus compartimentos solidificam-se a 0 °C.
  (C) é necessário, para utilização de seu potencial como reservatório de água potável, conhecer detalhadamente o aqüífero.
  (D) a água é adequada ao consumo humano direto em grande parte da área do compartimento Norte-Alto Uruguai.
  (E) o uso das águas do compartimento Norte-Alto Uruguai para irrigação deixaria ácido o solo.
```

## P7521-Q025
- recorte: `_banco/pendentes/enem2000a2008/P7521-Q025.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
{{img:1}}

intervalo.

O gráfico acima representa, de forma genérica, o que acontece com a quantidade de fármaco no organismo humano ao longo do tempo.

{{fonte:1}}

A meia-vida do antibiótico amoxicilina é de 1 hora. Assim, se uma dose desse antibiótico for injetada às 12 h em um paciente, o percentual dessa dose que restará em seu organismo às 13 h 30 min será aproximadamente de
  (A) 10%.
  (B) 15%.
  (C) 25%.
  (D) 35%.
  (E) 50%.
```

## P7521-Q034
- recorte: `_banco/pendentes/enem2000a2008/P7521-Q034.png`
- motivos: figura na pág. 13 depois da alternativa E foi descartada (não faz parte da questão) — conferir; há texto depois das alternativas (“**Aumento de produtividade** Nos últimos 60 anos, ”): conferir se é desta questão

```
{{img:1}}

**Temperatura do pescado nas peixarias**

Associação Brasileira de Defesa do Consumidor (com adaptações).

{{fonte:1}}

Uma das principais causas da degradação de peixes frescos é a contaminação por bactérias. O gráfico apresenta resultados de um estudo acerca da temperatura de peixes frescos vendidos em cinco peixarias. O ideal é que esses peixes sejam vendidos com temperaturas entre 2 ºC e 4 ºC. Selecionando-se aleatoriamente uma das cinco peixarias pesquisadas, a probabilidade de ela vender peixes frescos na condição ideal é igual a
  (A) \(\frac{1}{2}\) .
  (B) \(\frac{1}{3}\) .
  (C) \(\frac{1}{4}\) .
  (D) \(\frac{1}{5}\) .
  (E) \(\frac{1}{6}\) .

**Texto para as questões 35 e 36**
```

## P7523-Q008
- recorte: `_banco/pendentes/enem2000a2008/P7523-Q008.png`
- motivos: imagem 1 pode estar cortada (o desenho continua fora do recorte) — conferir

```
{{img:1}}

**Ministério do Meio Ambiente. Cadastro Nacional de Unidades de Conservação.**

Analisando-se os dados do gráfico acima, que remetem a critérios e objetivos no estabelecimento de unidades de conservação no Brasil, constata-se que
  (A) o equilíbrio entre unidades de conservação de proteção integral e de uso sustentável já atingido garante a preservação presente e futura da Amazônia.
  (B) as condições de aridez e a pequena diversidade biológica observadas na Caatinga explicam por que a área destinada à proteção integral desse bioma é menor que a dos demais biomas brasileiros.
  (C) o Cerrado, a Mata Atlântica e o Pampa, biomas mais intensamente modificados pela ação humana, apresentam proporção maior de unidades de proteção integral que de unidades de uso sustentável.
  (D) o estabelecimento de unidades de conservação deve ser incentivado para a preservação dos recursos hídricos e a manutenção da biodiversidade.
  (E) a sustentabilidade do Pantanal é inatingível, razão pela qual não foram criadas unidades de uso sustentável nesse bioma.
```

## P7523-Q021
- recorte: `_banco/pendentes/enem2000a2008/P7523-Q021.png`
- motivos: figura na pág. 9 depois da alternativa E foi descartada (não faz parte da questão) — conferir; há texto depois das alternativas (“O diagrama abaixo representa, de forma esquemática”): conferir se é desta questão

```
O *tangram* é um jogo oriental antigo, uma espécie de quebra-cabeça, constituído de sete peças: 5 triângulos retângulos e isósceles, 1 paralelogramo e 1 quadrado. Essas peças são obtidas recortando-se um quadrado de acordo com o esquema da figura 1. Utilizando-se todas as sete peças, é possível representar uma grande diversidade de formas, como as exemplificadas nas figuras 2 e 3.

{{img:1}}

{{fonte:1}}

Se o lado AB do hexágono mostrado na figura 2 mede 2 cm, então a área da figura 3, que representa uma “casinha”, é igual a
  (A) 4 cm<sup>2</sup>.
  (B) 8 cm<sup>2</sup>.
  (C) 12 cm<sup>2</sup>.
  (D) 14 cm<sup>2</sup>.
  (E) 16 cm<sup>2</sup>. **Diagrama para as questões 22 e 23**
```

## P7523-Q040
- recorte: `_banco/pendentes/enem2000a2008/P7523-Q040.png`
- motivos: imagem 1 pode estar cortada (o desenho continua fora do recorte) — conferir; 10 alternativas encontradas (esperado 5); letras fora de ordem: AABBCCDDEE; alternativas fora do padrão A–E

```
{{img:1}}

para o mar pela força dos ventos do noroeste.

II O argumento embasado na influência dos ventos do noroeste nas cheias do Nilo sustenta-se no fato de que, quando os ventos param, o rio Nilo não sobe.

III A explicação de alguns gregos para as cheias do

Nilo baseava-se no fato de que fenômeno igual ocorria com rios de menor porte que seguiam na mesma direção dos ventos.

É correto apenas o que se afirma em

Entre os seguintes ditos populares, qual deles melhor corresponde à figura acima?
  (A) Com perseverança, tudo se alcança.
  (A) I.
  (B) Cada macaco no seu galho.
  (B) II.
  (C) Nem tudo que balança cai.
  (C) I e II.
  (D) Quem tudo quer, tudo perde.
  (D) I e III.
  (E) Deus ajuda quem cedo madruga.
  (E) II e III.
```

## P7523-Q044
- recorte: `_banco/pendentes/enem2000a2008/P7523-Q044.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
O índice de massa corpórea (IMC) é uma medida que permite aos médicos fazer uma avaliação preliminar das condições físicas e do risco de uma pessoa desenvolver certas doenças, conforme mostra a tabela abaixo.

{{img:1}}

Internet: <www.somatematica.com.br>.

Considere as seguintes informações a respeito de João, Maria, Cristina, Antônio e Sérgio.

{{img:2}}

Os dados das tabelas indicam que
  (A) Cristina está dentro dos padrões de normalidade.
  (B) Maria está magra, mas não corre risco de desenvolver doenças.
  (C) João está obeso e o risco de desenvolver doenças é muito elevado.
  (D) Antônio está com sobrepeso e o risco de desenvolver doenças é muito elevado.
  (E) Sérgio está com sobrepeso, mas não corre risco de desenvolver doenças.
```

## P7523-Q063
- recorte: `_banco/pendentes/enem2000a2008/P7523-Q063.png`
- motivos: imagem 1 tem texto dentro (fórmula, esquema ou tabela) — conferir se não deveria ser texto

```
{{img:1}}

Suponha que o universo tenha 15 bilhões de anos de idade e que toda a sua história seja distribuída ao longo de 1 ano — o calendário cósmico —, de modo que cada segundo corresponda a 475 anos reais e, assim, 24 dias do calendário cósmico equivaleriam a cerca de 1 bilhão de anos reais. Suponha, ainda, que o universo comece em 1.º de janeiro a zero hora no calendário cósmico e o tempo presente esteja em 31 de dezembro às 23 h 59 min 59,99 s. A escala abaixo traz o período em que ocorreram alguns eventos importantes nesse calendário.
  (A) 1.
  (B) 2.
  (C) 3.
  (D) 4.
  (E) 5.
```
