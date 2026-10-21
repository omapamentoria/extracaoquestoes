# Instruções para o Gemini: estilos de questão do Banco MAPA

Você vai criar e aplicar os **estilos de questão** do banco de questões da plataforma MAPA. As 26 mil questões já
estão classificadas em área → matéria → assunto → subassunto. Agora cada **subassunto** ganha um nível a mais, o
**estilo de questão**. Com ele, a plataforma vai dizer ao aluno, por exemplo: *"em Juros, você erra mais as questões
que pedem a taxa"*.

Siga este documento à risca. Um programa confere cada arquivo antes de ele entrar na plataforma e recusa o que estiver
fora do formato.

## 1. Onde está tudo (repositório `omapamentoria/banco-de-questoes`, ramo `comentarios-gemini`)

```
estilos/
  INSTRUCOES.md                        ← este arquivo
  taxonomia.txt                        ← área > matéria > assunto > subassunto (códigos e nomes)
  indice.json                          ← lista dos 370 subassuntos: código, nome, assunto, matéria, nº de questões e de partes
  exemplos/A002-05.json                ← 3 subassuntos já feitos, para você copiar o padrão
  exemplos/A030-04.json
  exemplos/A085-01.json
  questoes/<SUBASSUNTO>/parte_01.json  ← as questões do subassunto, até 150 por parte
  questoes/<SUBASSUNTO>/parte_02.json  ← (só nos subassuntos grandes)
  respostas/<SUBASSUNTO>/lista.json    ← SUA lista de estilos do subassunto
  respostas/<SUBASSUNTO>/parte_01.json ← SUA atribuição de estilo a cada questão da parte 01
```

Cada questão em `parte_NN.json` traz:
- `id`;
- `vest` e `ano`;
- `texto`: o enunciado resumido (com "[…]" onde foi cortado), seguido de `||` e das alternativas;
- `gabarito`.

## 2. O que é um estilo

É **o que a questão pede e o passo de raciocínio que decide o acerto**. Não é o tema do texto de apoio. Duas questões
do mesmo estilo exigem o mesmo raciocínio, mesmo com contextos diferentes.

- Exemplos em Juros: "Calcula o montante ou os juros", "Calcula a taxa de juros", "Calcula o tempo da aplicação",
  "Compara aplicações ou formas de pagamento".
- Exemplos em Estequiometria: "Calcula massa ou mols pela proporção da reação", "Aplica rendimento, pureza ou teor",
  "Identifica reagente limitante ou em excesso".
- Exemplos em Interpretação de texto: "Localiza informação explícita no texto", "Infere informação implícita",
  "Identifica a crítica ou o humor do texto", "Reconhece a finalidade do texto".

Antes de começar, **abra os 3 arquivos de `estilos/exemplos/`**: eles mostram o tamanho, o jeito de nomear e as
descrições que a gente quer.

## 3. Regras da lista de estilos

1. **De 2 a 8 estilos** por subassunto. Subassunto com menos de 15 questões pode ter 1 ou 2.
2. Estilos que **não se sobrepõem** e que, juntos, cobrem quase todas as questões. O que não couber vai para um estilo
   **"Outros"**, que só existe se for necessário e não pode passar de **10%** das questões do subassunto.
3. Cada estilo precisa ter, se possível, **pelo menos 5 questões**. Se tiver menos, junte com o estilo mais parecido.
4. **Nome**: curto (até ~45 caracteres), que o aluno entenda, começando por verbo quando der. Exemplos: "Calcula a
   taxa de juros", "Interpreta a ironia do texto", "Relaciona massa e volume de gás".
5. **Descrição**: uma frase que diz o que caracteriza o estilo e **como diferenciá-lo dos vizinhos** (é ela que guia
   a atribuição).
6. O estilo **não pode** depender do vestibular, do ano nem do tema do texto ("questões do ENEM", "texto sobre
   meio ambiente" não são estilos).
7. Nomes sempre em português, mesmo em Inglês e Espanhol (ex.: "Identifica o sentido de uma expressão").
8. **Códigos**: `<SUBASSUNTO>-E1`, `-E2`… na ordem do mais comum para o menos comum. O estilo "Outros", se existir,
   é sempre `<SUBASSUNTO>-E9`.

## 4. Como trabalhar, um subassunto por vez

1. Abra `estilos/indice.json` e pegue o **próximo subassunto que ainda não tem `estilos/respostas/<SUB>/lista.json`**,
   na ordem do índice.
2. Leia as questões do subassunto:
   - até 3 partes: leia **todas** as partes antes de criar a lista;
   - mais de 3 partes: crie a lista lendo as partes 01, 02 e 03, e depois aplique a mesma lista às demais.
3. Crie a lista de estilos seguindo a seção 3 e grave `estilos/respostas/<SUB>/lista.json`.
4. Para **cada** parte, leia **questão por questão** e escolha **um** estilo principal para cada uma. Grave
   `estilos/respostas/<SUB>/parte_NN.json` (mesmo número da parte). Não use regra por palavra-chave: decida pelo que a
   questão realmente pede.
5. Depois que a `lista.json` de um subassunto estiver gravada, **não mude os códigos nem a ordem**. Se, numa parte
   seguinte, aparecer um estilo realmente novo, acrescente-o no fim da lista com o próximo número livre (sem reusar o E9).
6. Mensagem do commit: `Estilos de <SUB>`. Não altere nenhum arquivo fora de `estilos/respostas/`, nunca apague nada e
   não mexa em outros ramos.
7. **Se não puder gravar no GitHub**, responda com o conteúdo de cada arquivo em blocos `json` separados, cada um com o
   caminho do arquivo escrito logo acima.

Pode fazer vários subassuntos seguidos na mesma conversa, sempre um de cada vez e gravando cada um antes do próximo.

## 5. Formato dos arquivos de resposta

`estilos/respostas/A002-05/lista.json`:

```json
{
  "subassunto": "A002-05",
  "estilos": [
    {"codigo": "A002-05-E1", "nome": "Calcula o montante ou os juros", "descricao": "Pede o valor final (montante) ou os juros de uma aplicação/empréstimo dados capital, taxa e tempo."},
    {"codigo": "A002-05-E2", "nome": "Calcula o capital ou valor presente", "descricao": "Pede o valor inicial aplicado ou o valor presente de uma dívida, dados montante, taxa e tempo."},
    {"codigo": "A002-05-E9", "nome": "Outros", "descricao": "Questões que não se encaixam nos estilos acima (máximo de 10%)."}
  ]
}
```

`estilos/respostas/A002-05/parte_01.json`, com um objeto por questão da parte, na mesma ordem e sem pular nenhuma:

```json
[
  {"id": 100123, "estilo": "A002-05-E1"},
  {"id": 100456, "estilo": "A002-05-E7"}
]
```

O JSON tem que ser válido: aspas duplas, sem vírgula sobrando e sem comentários.

## 6. Antes de gravar, confira

- [ ] A lista tem de 2 a 8 estilos (fora o "Outros"), sem sobreposição, cada um com nome curto e descrição.
- [ ] "Outros" (E9) tem no máximo 10% das questões do subassunto.
- [ ] Cada `parte_NN.json` tem **todas** as questões da parte, na mesma ordem, cada uma com um código que existe na
      `lista.json`.
- [ ] Nada de estilo por vestibular, ano ou tema do texto.
- [ ] Arquivos gravados em `estilos/respostas/<SUB>/` no ramo `comentarios-gemini`.
