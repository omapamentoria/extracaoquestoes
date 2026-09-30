# Resolução comentada pelo Gemini: como usar

Tudo fica no repositório `omapamentoria/banco-de-questoes`, no ramo **`comentarios-gemini`**. Esse ramo é separado e
não mexe no banco nem na plataforma.

* Regras completas para o Gemini: `comentarios/INSTRUCOES.md`
* 719 lotes de 30 questões, com as figuras: `comentarios/lotes/lote_0000` … `lote_0718`.
  O lote 0000 tem os 16 comentários antigos a refazer, porque o gabarito antigo estava errado.
* As respostas do Gemini ficam em `comentarios/respostas/lote_NNNN.json`.

## Prompt para colar no Gemini (troque só o número do lote)

```
Você está conectado ao repositório GitHub omapamentoria/banco-de-questoes, ramo comentarios-gemini.
1. Leia o arquivo comentarios/INSTRUCOES.md inteiro e siga cada regra dele à risca.
2. Faça a resolução comentada do lote 0001: as questões estão em comentarios/lotes/lote_0001/questoes.json e as
   figuras (.webp) estão na mesma pasta. Abra cada figura antes de resolver a questão que a usa.
3. Grave a resposta em comentarios/respostas/lote_0001.json, no ramo comentarios-gemini, com a mensagem
   "Comentários do lote 0001". Não altere nenhum outro arquivo.
   Se você não puder gravar no GitHub, responda só com o conteúdo do arquivo, num único bloco json.
Lembre: o gabarito é o oficial e não se discute; nada inventado; figura que você não conseguiu ver = "sem_imagem";
se discordar do gabarito = "discordo", sem comentário. Confira a lista da seção 6 antes de gravar.
```

Para os lotes seguintes, repita o mesmo prompt trocando o número. Se o Gemini aguentar, dá para pedir
"faça os lotes 0001 a 0003, um arquivo por lote".

## Depois

* Rodar `python3 ferramentas_nuvem/confere_comentarios.py <pasta do ramo comentarios-gemini>`.
  Ele gera `docs/comentarios-conferencia.md` com três listas: os aceitos, os lotes a refazer e os casos para revisão
  humana (discordo, sem imagem, incompleta).
* Quando a classificação estiver pronta, rodar
  `COMENTARIOS=<pasta do ramo> python3 ferramentas_nuvem/converte.py <Banco-de-questoes>`.
  Ele coloca os comentários aceitos nas questões sem comentário, e só quando o gabarito da questão continua o mesmo
  para o qual o comentário foi escrito. Depois disso a classificação é aplicada e tudo vai junto para a plataforma.
