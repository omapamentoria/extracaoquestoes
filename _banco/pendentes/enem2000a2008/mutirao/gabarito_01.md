# Mutirão enem2000a2008 — gabarito (1 questões)

Sem gabarito. NÃO invente: só marque _fora com o motivo se o gabarito oficial da mesma cor não traz a questão.

Formato da resposta (um objeto JSON; junte ao `ferramentas_nuvem/fabrica/correcoes/enem2000a2008.json`):
```json
{"<origem>": {"motivo": "o que foi lido no recorte", "statement_sub": [["regex que acha o trecho", "texto certo"]],
              "alt_sub": {"B": ["regex", "texto"]}, "alternativas": {"C": "texto inteiro"}, "remove_imagens": [2]},
 "_fora": {"<origem>": "motivo (só se for impossível ter certeza)"},
 "_casa": {"<origem>": [<id no banco>, "motivo"]}}
```
Regras: cópia fiel do recorte, nada inventado. Na dúvida, `_fora` com o motivo. Nunca mude o gabarito.

## P7519-Q046
- recorte: `_banco/pendentes/enem2000a2008/P7519-Q046.png`
- motivos: sem gabarito (resposta esperada); alternativas fora do padrão A–E; sem gabarito; o extrator não leu a letra desta questão (o oficial tem)

```
No primeiro semestre de 2006, o Movimento Global pela Criança, em parceria com o UNICEF, divulgou o relatório Salvando vidas: o direito das crianças ao tratamento de HIV e AIDS. Nesse relatório, conclui-se que o aumento da prevenção primária ao vírus deverá reduzir o número de novos casos de infecção entre jovens de 15 a 24 anos de idade, como mostra o gráfico a seguir.

{{img:1}}

Com base nesses dados, analise as seguintes afirmações.

I Ações educativas de prevenção da transmissão do vírus

HIV poderão contribuir para a redução, em 2008, de mais de 20% dos novos casos de infecção entre os jovens, em relação ao ano de 2005.

II Ações educativas relativas à utilização de preservativos

nas relações sexuais reduzirão em 25% ao ano os novos casos de AIDS entre os jovens.

III Sem o aumento de medidas de prevenção primária,

estima-se que, em 2010, o aumento de novos casos de infecção por HIV entre os jovens será, em relação ao ano de 2005, 50% maior.

É correto apenas o que se afirma em

```
