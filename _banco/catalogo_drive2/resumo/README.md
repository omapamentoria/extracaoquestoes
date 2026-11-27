# Catálogo automático do Drive novo (fábrica, etapa 1) — 27/11/2026

Feito só por script, sem IA (`ferramentas_nuvem/fabrica/analisa_drive2.py` + `monta_catalogo.py`), a partir da pasta
`1XaHPSOkJqjAYt3CifEZ71jopiWGWEjT8`: 3.928 arquivos, baixados um por um pelo ID, medidos e apagados.

- Um arquivo por instituição: `_banco/catalogo_drive2/drive2_<instituicao>.json`, no mesmo formato do catálogo antigo,
  com códigos **P6000–P9885** (os 42 arquivos do ENEM 2020–2025 que já tinham código ficam com o código antigo).
  Campos novos: `drive_id`, `cor_triagem`, `triagem_motivos`, `gabarito_confere`, `questoes_faixa`, `outra_cor_de`,
  `ja_no_drive_antigo` (mesmo arquivo, byte a byte, que já estava no Drive antigo).
- Números por instituição: `resumo_drive2.json`.
- Os códigos ficam fixos: rodar de novo mantém o código de quem já tem.

## Como o script decide

- **Papel:** pelo nome e pela pasta (gabarito, resolução, padrão de resposta, redação), corrigido pelo conteúdo
  (arquivo curto cheio de "número + letra" é gabarito).
- **Ligação prova → gabarito:** mesma pasta (ou vizinha), mesmo ano. Se dia, fase, módulo, cor ou versão aparecerem
  nos dois nomes e forem diferentes, não liga. Conteúdo: cada número do gabarito tem que aparecer como início de
  questão na prova (`gabarito_confere`: sim / contém = o gabarito cobre mais coisa / não / ? = não li o gabarito).
- **Repetidos:** mesmo md5. **Mesma prova em várias cores:** fica uma (a azul, se der) e as outras ficam de reserva.
- **Cor de triagem** (é estimativa; a extração confere o gabarito de novo, questão por questão):
  - verde: tem texto, gabarito ligado e conferido pelo conteúdo, sem alerta;
  - amarelo: gabarito ligado, mas com alerta (o gabarito cobre outro dia ou caderno, símbolos desenhados, páginas sem texto,
    dois gabaritos possíveis, a prova parece ter parte discursiva);
  - vermelho: sem gabarito, prova escaneada, gabarito em formato que o script não lê (somatória da UEM/UFSC/UEPG,
    certo/errado da UnB), número de questões que não bate;
  - discursiva: fica fora das três cores.
