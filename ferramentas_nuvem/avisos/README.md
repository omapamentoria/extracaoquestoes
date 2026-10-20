# Avisos dos alunos → correção no banco

Ferramentas da rodada de outubro de 2026 (PR omapamentoria/Banco-de-questoes#6). Base da rotina automática.

Todos recebem a pasta de trabalho `<av>` com `partes/` (cópia de `final/partes` do ramo padrão), `rep/` (avisos),
`pdf/` e `gabs/` (PDFs baixados do Drive por `ferramentas_nuvem/mapa_drive.json`).

| Script | O que faz |
|---|---|
| `audita_gab.py` | baixa cada gabarito ligado a cada prova e mede a concordância com o banco |
| `gabh.py` | leitor de gabarito em tabela horizontal (USS) |
| `sas_gab.py` | lê "Resposta correta: X" das resoluções SAS, coluna por coluna (aceita `PROVA=GABARITO`) |
| `sas_confere.py` | confere pelo conteúdo se o bloco da resolução é da mesma questão |
| `gab_fix.py` | provas que usaram o gabarito da prova vizinha (FATEC 2º sem., USS, UNESP 2022) |
| `note_adote.py`, `note_aplica.py` | separa o "Note e adote" das alternativas (FUVEST) |
| `realinha.py` | realinha alternativas deslocadas pelo início de cada alternativa no PDF |
| `aplica.py` | aplica tudo nas partes e separa a quarentena |
| `manual.py` | correções conferidas à mão e comentários a refazer |

Regras: gabarito só do oficial da própria prova; o que não confirma vai para a quarentena; comentário escrito sobre
gabarito errado é apagado.
