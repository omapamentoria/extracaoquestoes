# Pendências do banco de questões

Lista só do banco de questões. O Matheus acrescenta itens quando quiser (direto no GitHub: botão de lápis, escrever,
"Commit changes"). Quando um item for resolvido, ele sai daqui e vai para o HANDOFF.

## Faltam arquivos (o Matheus consegue e põe no Drive)

| Prova | O que falta | Por que importa |
|---|---|---|
| ENEM 2010 regular, dias 1 e 2 | Gabarito oficial do INEP (caderno amarelo) | Sem ele a prova não entra inteira. O "(Gabarito)" do dia 1 no Drive é o caderno com as respostas circuladas, e o do dia 2 é o gabarito de 2009. |
| ENEM 2019 PPL/reaplicação, dias 1 e 2 | Prova e gabarito (não estão no Drive novo) | As 128 questões dela no banco antigo seguem sem prova completa. |
| ENEM 2021 PPL/reaplicação | Prova e gabarito no Drive novo (só existem no Drive antigo) | Prova ainda não está inteira no banco. |
| ENEM 2022 PPL/reaplicação | Prova e gabarito no Drive novo (só existem no Drive antigo) | Prova ainda não está inteira no banco. |
| ENEM 2020 digital, dia 1 | Caderno com o Espanhol | As 4 questões de espanhol (4850, 4943, 4981, 5024) não estão no caderno do Drive novo. |

## Decisões do Matheus

- **Questão 1042** (ENEM 2011 PPL, dia 2, questão 163): o gabarito do arquivo oficial diz **B** (= 1), mas a conta dá
  **D** (1/4). No banco está D, fora da prova completa. Em 28/11 o Matheus pediu para manter o oficial; antes de
  trocar, confirmar com ele (ver a explicação na conversa de 28/11).

## A fazer (trabalho do Claude)

- ENEM 2000–2008 (9 provas): extrair com a estratégia nova (mais barata).
- Questões 2261 e 2477 (ENEM 2014, banco antigo): não são das provas do Drive novo (outra aplicação ou dia).
- Simulados marcados como prova oficial no banco: conferir e corrigir.
- Questões novas sem comentário (ENEM 2009–2025): falta mandar os lotes ao Gemini.
- Plataforma: o Lovable ainda não usa os campos `prova_completa*` ("fazer a prova inteira").
- Catálogo do Drive novo: 1.030 provas vermelhas (sem gabarito, escaneadas, gabarito em formato que o script não lê) e
  169 discursivas, para depois das verdes e amarelas (`_banco/catalogo_drive2/resumo/`).
