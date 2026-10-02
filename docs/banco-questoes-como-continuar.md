# Banco MAPA — como continuar o trabalho (instruções para o Claude)

Leia isto antes de qualquer sessão de extração. Leia também:

* `banco-questoes-plano.md`
* `banco-questoes-produto-final.md` (REGRA DE OURO: cópia fiel, nada inventado)
* `banco-questoes-pendencias.md`

> **Nota (sessão Claude Code na nuvem, 28/09/2026):** a partir daqui o trabalho roda numa
> sessão Claude Code na nuvem, sem acesso ao notebook. Os arquivos vêm do Google Drive
> (pastas compartilhadas por link) com `ferramentas_nuvem/drive_sync.py` e ficam em
> `~/mnt/BM/` (mesma estrutura do notebook). Código, transcrições e resultados são
> guardados neste repositório GitHub, pois o disco da sessão é apagado ao fim dela.
> As seções sobre `device_bash`, `device_stage_files` e `device_commit_files` abaixo
> valem só para a sessão antiga (Cowork no notebook).

## Ambiente (atualizado em 28/09/2026)

### Quem faz o quê

* O Matheus é leigo em programação e segue instruções passo a passo. Todo o código e toda a execução ficam com o Claude.
* O plano é Claude Pro, sem API, então é preciso economizar cota. O Python faz o máximo possível; o Claude só olha as páginas que o código não resolve.

### Onde estão os PDFs e como rodar

* Os PDFs ficam no notebook do Matheus (Windows), em `C:\BM`. Essa pasta precisa estar conectada na sessão ("Add folder").
* Há shell no notebook (`device_bash`). O Python roda direto lá, em `$HOME/mnt/BM`, sem copiar PDFs para a nuvem.
* Só usar `device_stage_files` quando o Claude precisar VER uma página (como imagem) ou usar uma ferramenta que só existe na nuvem.
* Já instalado no notebook: Python 3.10, poppler (`pdftotext`, `pdfinfo`, `pdftoppm`), pdfplumber, openpyxl, numpy, OpenCV (`cv2`) e tesseract (só inglês). Não há PyMuPDF nem scipy.

### Limites do `device_bash`

* Cada chamada dura no máximo ~175 s, e processos em segundo plano morrem no fim da chamada. Por isso, scripts longos têm de ser retomáveis.
* Usar `Pool(2)` (são 2 núcleos).
* O ENEM (P2605) leva ~170 s na v136: rodar uma prova por chamada. Para escalar, o 06 precisa ficar retomável por página, ou as provas devem rodar na nuvem.
* O `device_bash` não pode apagar arquivos da pasta conectada. Arquivos temporários vão em `~/tmp_banco` (fora de `mnt`).
* Os nomes de pasta vêm em Unicode decomposto (NFD). Normalizar com `unicodedata.normalize("NFC", ...)` antes de comparar texto.

### Rodar na nuvem (desde o Piloto 2, 28/09/2026)

* A extração agora roda no ambiente do Claude (nuvem): ~50 s por prova de 90 questões, contra ~170 s no notebook, com resultado idêntico (conferido no ENEM 2023 e no SSA 2025).
* Estrutura na nuvem, igual à do notebook: `~/mnt/BM/<caminho do catálogo>` e `~/mnt/BM/_banco/` (catalogo_debug.json, vocab.json.gz, glifos_ref.json, transcricoes/, codigo/).
* Os PDFs de cada lote são trazidos com `device_stage_files` (ficam em `/mnt/user-data/uploads/BM/...`) e copiados para `~/mnt/BM/...`. Trazer também os gabaritos, inclusive os da mesma pasta (o código procura gabarito trocado entre os irmãos).
* O código mestre fica na nuvem, em `~/mnt/BM/_banco/codigo/` (`06_extrair.py` + `glifos_t3.py`). Ao fim de cada sessão, mandar para o notebook (commit de `_vN.py`, depois `cp`). Última versão: `_v138.py`, mais `glifos_t3.py` e `_banco/glifos_ref.json` (no notebook também como `glifos_t3_v138.py` e `glifos_ref_v138.json`, já copiados por cima dos antigos).
* Ferramentas (cópia no notebook em `_banco/ferramentas/`; na nuvem, em `~/tmp_banco/`):
  * `roda.sh PID...`: roda as provas, 2 de cada vez;
  * `snap.py PID...` e `diff.py PID...`: base de regressão por prova;
  * `resumo.py PID`: alertas mais comuns e textos-base;
  * `pacote.py <pasta> PID...`: monta a página de revisão (index.html do rev1, dados.json e imagens em jpg);
  * `rotula.py <pasta da prova> "0=β" "1=→"`: acrescenta glifos conferidos por visão à tabela;
  * `prep_vis.py PID Qnnn...`: gera, para cada questão PENDENTE, o recorte da página a 200 dpi e a extração atual (`~/tmp_banco/vis/`), para a transcrição por visão;
  * `chk_ids.py`: confere se os `{{img:k}}` das transcrições ainda apontam para as mesmas imagens depois de mudar o código (rodar antes de gravar em `transcricoes/`).
* Transcrição por visão: `prep_vis.py` → subagentes (até 8 questões cada) escrevem JSON → Claude confere uma amostra na imagem → `chk_ids.py` → grava `transcricoes/<PID>.json`. Nunca aceitar texto de alternativa inventado ("figura da linha a"); se a alternativa é desenho, o código tem de recortar.
* Uma página de revisão aceita no máximo 511 arquivos por versão e 255 por publicação: agrupar 2 ou 3 provas por página.

### Como mandar código para o notebook

* Pegadinha: `device_commit_files` só funciona para um nome de arquivo NOVO. Sobrescrever um arquivo existente manda a versão velha.
* Fluxo:
  1. Na nuvem, copiar o script para `vN.py`.
  2. Fazer commit para `codigo/_vN.py`.
  3. No notebook, rodar `cp codigo/_vN.py codigo/06_extrair.py`.
* Última versão: `_v138.py` (+ `glifos_t3.py`, carregado pelo 06). Para arquivos de apoio que já existem (glifos_t3.py, glifos_ref.json), fazer commit com nome novo (`_v138`) e `cp` por cima.

### Página de revisão

* A nuvem não acessa o cdnjs, então não dá para testar o MathJax localmente. A página publicada carrega o MathJax 3.2.2 (delimitadores `\( \)`).
* Para screenshots locais, usar `http.server` (porta 8765) + Playwright, com as imagens forçadas a `loading=eager` e espera de 2,5 s. Com carregamento lento, os recortes aparecem em branco e dão falso erro.

### Teste de regressão (obrigatório antes de publicar)

* No notebook, em `~/tmp_banco`:
  * `snap.py` salva a base: imagens, texto, alternativas e fontes de cada questão (`base_enem.json`, `base_ssa.json`).
  * `diff.py enem|ssa` lista o que mudou em relação à base.
* Toda mudança listada tem de ser olhada (imagem e texto) antes de aceitar. Quando estiver tudo certo, rodar `snap.py` de novo para atualizar a base.
* Subagentes que conferem imagens às vezes erram (ex.: o falso "palavra sumida" na Q148). Sempre confirmar o que eles apontam.

## O que já existe em `C:\BM\_banco`

* `catalogo.xlsx`: a planilha para o Matheus (abas Resumo, A extrair, Conferir, Catálogo completo).
* `catalogo.csv` (separador `;`, UTF-8 com BOM) e `catalogo_debug.json`: a mesma tabela, para os scripts.
* Arquivos de apoio:
  * `inventario.jsonl`
  * `texto/<md5>.txt.gz` (texto completo de cada PDF)
  * `legibilidade.jsonl`
  * `similares.jsonl`
  * `vocab.json.gz` (vocabulário usado para decidir o hífen de fim de linha)
* `codigo/`:
  * Catálogo, nesta ordem: `01_inventario.py` → `02_classificar.py` → `03_texto.py` → `04_similaridade.py` → `02_classificar.py` (de novo) → `05_planilha.py`.
  * Extração: `06_extrair.py <id>` (formato reconhecido sozinho; `enem`/`ssa` no 2º argumento só forçam o fluxo).
  * Revisão: `07_pacote_revisao.py <id> <id>...` (gera `piloto/pacote_revisao.zip`).
* `questoes/<vestibular>/<ano>/<id_prova>/`:
  * `questoes.json`, `textos_base.json`, `textos_nao_ligados.json`
  * `img/` (figuras a 300 dpi)
  * `revisao/` (recortes da página para conferência)
* `transcricoes/<id_prova>.json`: trechos que o PDF não tem como texto (letras desenhadas como curvas, layout em 3 colunas), transcritos pelo Claude lendo a imagem.
  * As chaves são por questão (`Q038`, `Q020-ING`), com os campos `enunciado`, `fontes`, `alternativas` {A..E} e `nota`.
  * O extrator aplica a transcrição e deixa um alerta "conferir".

## Extrator (`06_extrair.py`), v139 (29/09/2026)

* Estilos de cabeçalho novos, que só vencem se formam sequência maior que os antigos: `questao_nb` ("QUESTÃO 4" sem negrito; "Questão 92 - Ciências…" vira área), `grande` (número grande solto; rótulo "Questão" ao lado sai da linha) e `lead` ("08 Um funcionário…", número em negrito ou maior). Dígitos separados pela fonte ("9 2") são juntados.
* Modo OCR: se existe `~/mnt/BM/_ocr/<PID>.pdf` (`ferramentas_nuvem/ocr_pdf.py PID...`), ele é lido no lugar do PDF original. Fundo do papel limpo, bolinhas de alternativa do ENEM achadas na imagem (`<PID>.bolhas.json`), negrito medido pela espessura do traço, faixa das linhas de texto fora das figuras; toda questão recebe alerta de OCR. Nada disso age em prova sem o arquivo de OCR.
* `refaz_lista.py ocr [PID...]` (e `LOTE=nome` para não sobrescrever relatórios): OCR + extração das provas de texto ruim e de `docs/lotes/ocr_extra.txt`.
* Página de revisão das questões com alerta: `python3 ferramentas_nuvem/rev_alertas.py <pasta> PID...` (recortes e figuras embutidos em `dados/<PID>.json`; publicar em partes de até ~60 MB).
* Base de regressão: se `~/tmp_banco/base_*.json` não existe (sessão nova), rodar as 9 provas-base com o código do último commit e `snap.py` ANTES de mexer.

## Extrator (`06_extrair.py`), v138

### Novidades da v138 (Piloto 2, 2ª rodada)

* Tabela aberta (`tabela_aberta`): faixa de cabeçalho emoldurada + fio vertical entre colunas + fio de baixo = tabela inteira; a grade é montada com fios explícitos (`TAB_EXPL`). Item de lista na célula vira `<br>` (a página de revisão mostra `<br>`).
* Linha inteira dentro de uma tabela de dados vai para a tabela (a tabela nunca sai pela metade).
* Alternativas em tabela também quando as alternativas já foram lidas mas estão ao lado/dentro de uma grade (`alt_sobre_imagem`), inclusive quando a grade foi partida em uma imagem por linha (união das imagens); grade sem fio da direita ganha fio no fim do texto; cabeçalho solto acima da grade é lido por coluna. Só com 2+ colunas.
* Alternativas em células de uma imagem (`alternativas_em_celulas`): a grade da imagem é achada pelos fios, cada letra é lida sozinha pelo OCR e cada conteúdo vira um recorte. O corte do topo sobe até uma faixa branca (o radical da alternativa a não fica na figura).
* Marcador de alternativa só conta como "rótulo de foto" se não tem texto depois dele ("D) 7/23" não parte gráfico).
* Duas figuras não se juntam se a caixa única cobriria texto de nenhuma das duas (`texto_na_uniao`).
* Marca d'água girada fora das colunas é apagada da tinta. Pedaço de cabeçalho repetido que caiu em outra coluna ("2005") sai (`pedaco_rodape`).
* Capa com ficha do candidato (`RE_CAPA`) antes da 1ª questão fica fora.
* Desenho largo que atravessa o meio da página cria faixa de largura total (figura entre texto-base e colunas fica na ordem certa). Figura no alto de outra coluna, com o mesmo topo e altura de uma figura já lida, fica junto dela.
* Dentro de moldura de layout, desenho feito só de fios (grade com fios por dentro e sem outra tinta) não é apagado.
* Quadro de legenda só com moldura visível (retângulo branco de fundo não conta).
* Texto oculto: também 2+ palavras sem tinta no fim da linha ou separadas por vão de coluna.
* `(cid:N)`: a chave do glifo inclui tamanho e largura (o mesmo código pode ser "(" numa fonte e "+" noutra); traço curto vira "−" antes de dígito. Índice "−1" entra na linha em 2ª passada.
* Bloco de texto ao lado de figura (mesma esquerda) não é tratado como assinatura.
* Transcrição aceita `apos_alternativas`.

### Novidades da v137 (Piloto 2)

* Formato reconhecido pelo código (perfil `auto`): o cabeçalho da questão pode ser "QUESTÃO 91", "10. texto" ou um número sozinho em negrito ("4", "01" em caixa preta). Vence o estilo com a maior sequência 1, 2, 3… Também são reconhecidos: alternativas "A.", provas de 4 alternativas (a–d) e o fluxo (ENEM ou blocos com textos-base). Tudo é impresso na linha `formato:` do log.
* Uma regra só para alternativas (`letra_alt`) e para cabeçalhos (`eh_cabecalho`), usadas no código todo. `linha_estrutural` (cabeçalho, alternativa, "Texto para…", título de área, opção de língua) nunca vira figura.
* Enfeite do cabeçalho (caixa preta com o número, faixa cinza, barra listrada) não é figura.
* Logotipo repetido no alto ou no pé de várias páginas é removido antes da detecção de figuras (`LOGOS`).
* Textos-base:
  * Rótulo em frase: "Observe a imagem e leia o texto, para responder às questões de 14 a 16", "As questões 1 e 2 referem-se ao poema", mesmo quebrado em 2 linhas.
  * Versalete ("T EXTO") é juntado numa palavra só.
  * Um rótulo no alto da página não é tratado como cabeçalho repetido.
* Provas com cabeçalho explícito (caixa "07", "QUESTÃO 7"): o que vem depois da última alternativa fica na questão, a não ser que seja um rótulo de texto.
  * Esse trecho ("Note e adote", dados) vai para o campo `apos_alternativas` e é mostrado depois das alternativas.
  * Quando não parece dado da questão, entra um alerta.
* Fora do banco:
  * Páginas de redação/instruções antes da 1ª questão, ou no meio do caderno sem nenhuma questão.
  * "RASCUNHO".
  * Código interno de simulado (R387, 196SE02BIO2019II, "CALIBRADA MAT").
  * Texto invisível: camada oculta, como a resolução escondida no Bernoulli. Só sai a linha quase toda sem tinta.
  * Imagens que não aparecem na página renderizada.
* Rodapé:
  * Número sozinho no alto/pé só é número de página se acompanha a página. Número em negrito que não acompanha é número de questão (FUVEST).
  * Rodapé repetido em metade das páginas sai mesmo a 87–88% da altura.
* Parágrafos: o entrelinha é medido por região (moda). Resolve provas em que cada linha virava parágrafo.
* Figuras de alternativas: cada figura vai para a alternativa cujo marcador está ao lado ou logo acima dela. Uma linha com vários marcadores ("a) b) c)" em grade) vira várias alternativas.
* Alternativas em tabela (cada linha = uma alternativa): viram texto, cabeçalho + linha.
* Alternativas-gráfico numa imagem só (a) b) c)… dentro da foto, inclusive em grade): o OCR acha as letras e o código recorta uma imagem por alternativa. Só fica PENDENTE se o recorte tem altura de uma linha (texto desenhado).
* Gabarito:
  * Tabela horizontal ("Questão 1 2 3" / "Gabarito B A E").
  * Cartão de respostas desenhado (caixa cheia = resposta; vale mais que o texto).
  * Resolução comentada ("C) CORRETA").
  * Gabarito trocado de arquivo: procura na mesma pasta o que cobre as questões.
  * Alternativa marcada no caderno, só se UMA letra é bem mais escura que as outras.
* Glifos-imagem (fonte Type3, muito comum na FUVEST) e "(cid:N)" sem tabela de texto:
  * A forma de cada glifo é comparada com `_banco/glifos_ref.json`, uma tabela conferida por visão que vale para todas as provas.
  * Hífen, travessão e sinal de menos são decididos pelo contexto.
  * Sobrelinha de segmento nunca vira fração.
  * Fórmula montada com letras de glifo fica PENDENTE (transcrever por visão). Símbolo simples (×, ≈) só pede "conferir".
  * Glifo desconhecido vai para a folha `revisao/glifos_desconhecidos_*.png`. O Claude lê a folha e roda `rotula.py`.
* Depuração nova: `DEBUGQ=1` (candidatos a cabeçalho), `DEBUGCAB=<regex>` (cabeçalho/rodapé repetido), `ORDEM=<pág,pág>` (ordem de leitura).

### Regras que vêm do Piloto 1 (v136)

#### Leitura do texto

* Lê as palavras com fonte e tamanho (pdfplumber), agrupa em linhas e marca negrito/itálico e `<sup>`/`<sub>`.
* Caracteres duplicados são removidos (`dedupe_chars`).
* Na fonte Symbol, letras latinas viram gregas (a→α), exceto em palavras com "(cid:".
* Pontuação solta herda o tamanho da palavra vizinha.
* Texto girado (eixo de gráfico) não entra como palavra: fica como tinta da figura.
* A página é dividida em faixas de largura total ou de 2 colunas. Nenhuma faixa pode ficar sem região, senão o texto some.
* Cabeçalho e rodapé repetidos são removidos.
* Sublinhado vira `<u>…</u>`: traço fino colado embaixo da palavra, sem grade de tabela e sem denominador embaixo, para não confundir com barra de fração.
* Espaço antes de `)`, `]`, `,` e `.` e depois de `(` e `[` é removido quando a distância é pequena.

#### Números de parágrafo

* Número na margem (quadradinho ou dígito no início da linha) vai para o começo do parágrafo.
* O parágrafo-alvo é a primeira linha candidata que inicia parágrafo.

#### Matemática e química

* Matemática vira texto LaTeX entre `\( \)`:
  * fração empilhada: `\frac`
  * raiz: `\sqrt`, só quando tem formato de raiz (moldura ou borda não conta)
  * vetor: `\overrightarrow`, só com ponta
  * chapéu ou arco: `\widehat`
* Seta de reação: traço horizontal com ponta preenchida vira →, ← ou ↔. Duas setas empilhadas viram ⇌.

#### Parágrafos (`monta`)

* Constantes medidas na página: GAP_L (espaço típico entre linhas), MARGEM_DIR e BORDA_TIPICA por coluna (usada quando a região tem poucas linhas).
* Começa parágrafo novo quando há:
  * espaço grande entre linhas (> GAP_L + 0,18·corpo);
  * recuo;
  * linha curta com fim de frase;
  * troca entre linha centralizada e não centralizada;
  * assinatura alinhada à direita;
  * fim de lista.
* Verso/poema (grupo irregular, com no máximo 20% das linhas chegando à borda) mantém as quebras de linha.
* Marcadores (•) e falas em maiúsculas sempre quebram linha.
* A junção de hífen é decidida antes da quebra.
* Negrito partido entre linhas é unido.

#### Figuras: detecção

* A página é renderizada, o texto é apagado e o que sobra de tinta é gráfico.
* Uma ilustração = um recorte só:
  * Partes empilhadas ou lado a lado, sem texto no meio, viram uma imagem.
  * Uma linha de rótulos que atravessa duas figuras junta as duas.
  * Pedaço estreito (título de eixo girado) junta à figura vizinha.
* Figuras ao lado de alternativas diferentes (A–E) nunca se juntam, em nenhuma das regras de junção nem no crescimento.
* O texto da figura fica na figura: rótulo encostado, unidade, título em negrito centralizado logo acima e denominador de fração dentro do desenho. O recorte cobre a caixa inteira de cada palavra absorvida.

#### Figuras: recorte nunca cortado

* Tabela com grade visível entra inteira.
* Foto embutida no PDF entra com a caixa inteira, aparada onde passa por baixo de uma linha de texto.
* O recorte cresce quando um desenho grande continua para fora dele. Não cresce se isso engolir parágrafo, fonte, alternativa ou número de questão, mais de 3 linhas ou mais que 2× a área.
* O recorte não invade figura vizinha. A margem é de 3 pt, ou 1 pt onde há texto colado.
* Branqueamento: texto de fora que ficou dentro do recorte é pintado de branco. Isso só acontece se aquela linha já aparece no texto final da questão, para não apagar texto que só existe na imagem (ex.: meme da Q034).

#### Figuras: o que nunca vira imagem

* Linha de fonte ("Disponível em", "Acesso em", "Foto:", URL, fontes em espanhol/inglês) e suas continuações.
* Linha com 4+ palavras e sem desenho em volta.
* Parágrafo sem desenho perto.
* Quadradinho com número.
* Moldura ou tabela de layout que envolve texto + imagem: só a imagem vira figura, o texto sai como texto.

#### Legendas

* Linha curta ao lado de uma figura, alinhada à base dela, é legenda. Ela vai para logo depois da imagem, como parágrafo próprio.
* Alternativa, número de questão e linha só de números nunca são legenda.

#### Tabelas

* Tabelas com grade são transcritas quando validadas:
  * só há 1 tabela;
  * ela cobre a região;
  * só há texto das células (palavras fora da grade reprovam);
  * não há células longas;
  * não há imagem dentro.
* As células mantêm negrito e itálico.

#### Fontes (créditos)

* As fontes sempre vêm antes do comando. O marcador `{{fonte:N}}` fica onde a fonte aparece, e o parágrafo do comando é sempre o último.
* A continuação de uma fonte é decidida pela posição: a fonte cuja última linha está logo acima.
* Linha pequena seguida de "Disponível em" é título da fonte.

#### Textos-base

* `textos_base_ids`: textos ligados por "Texto para as questões X e Y" e textos citados pelo número ("Texto 7", "Textos 4 e 5"), respeitando a língua.
* O cabeçalho de área ("Questões de N a M") é sempre consumido como título e nunca entra numa questão.

#### Alertas e PENDENTES

* Alternativas sempre em texto. Alternativa que é só uma imagem da altura de uma linha é texto desenhado: alerta PENDENTE até entrar em `transcricoes/`. Linhas "(cid:" também geram PENDENTE ("trecho desenhado").
* Tinta no meio de uma linha de texto gera PENDENTE.
* Alertas automáticos:
  * alternativas idênticas;
  * texto curto solto ao lado de imagem;
  * recorte com desenho continuando para fora ("pode estar cortada");
  * linha não aproveitada.
* A lista "PENDENTES de transcrição por visão" tem de estar vazia antes de publicar.

#### Depuração

* `DEBUGF=1`: figuras, absorções, crescimento e legendas.
* `DEBUG=<pág>`: imagem em `piloto/tmp`.
* `DEBUGTXT=<regex>`: onde foi parar uma linha ou palavra.
* `DEBUGP=<regex>`: decisão de parágrafo.
* `DEBUGN=<pág>`: números de parágrafo.

## Como ler o catálogo

* `status`: `a extrair`, `apoio` (gabarito ou resolução usados junto com a prova), `ignorar (duplicata)` ou `ignorar (sem questões)`.
* `gabarito_ids`, `resolucao_ids` e `padrao_ids`: ids (Pxxxx) dos arquivos pareados com a prova.
* `texto`: `ok`, `parcialmente corrompido`, `corrompido` ou `sem_texto (imagem)`. Os três últimos precisam de visão/OCR.
* Atenção ENEM: o gabarito muda com a cor do caderno. Usar o gabarito da MESMA cor.

## Ordem de trabalho

1. ~~Catálogo completo~~ (26/09/2026).
2. ~~Piloto 1~~ (26–28/09/2026): ENEM 2023 dia 2 (P2605, 90 questões) e SSA 2025 1ª etapa dia 1 (P4011, 49 questões).
   * Tudo o que o Matheus apontou e a autorrevisão do Claude foi corrigido (v136).
   * Página de revisão: artefato "Revisão do Piloto MAPA", versão 13. Publicar de `/home/claude/rev1` (index.html + arquivos do zip, até 255 por publicação).
3. Piloto 2 (28/09/2026; 2ª rodada publicada, aguardando revisão): ENEM 2005 (P2400), ENEM PPL 2012 dia 2 (P2431), SSA 1 2018 dia 1 (P4083), Bernoulli 2019 nº 1 dia 2 (P3144), SAS 2021 nº 1 dia 1 (P3392), FUVEST 2017 1ª fase (P1108) e UNICAMP 2012 1ª fase (P2116).
   * Páginas de revisão: "Piloto 2 ENEM e SSA", "Piloto 2 Simulados" e "Piloto 2 FUVEST e UNICAMP" (publicar de `/home/claude/rev3A`, `rev3B` e `rev3C`, montadas com `pacote.py`; o index.html usado é `/home/claude/index_rev3.html` (o do rev2A com `<br>` liberado; cópia no notebook em `_banco/ferramentas/index_rev3.html`)).
   * Base de regressão re-tirada das 9 provas na v138 (P4011 mudou 8 itens aceitos: Q019 em 2 imagens, rótulos "Texto N" como texto).
   * Pergunta em aberto para o Matheus: números de linha na margem da FUVEST.
   * Base de regressão (`snap.py`) já tirada das 9 provas (Pilotos 1 e 2).
   * Problemas ainda abertos: ver `banco-questoes-pendencias.md` (seção Piloto 2).
4. Depois: escala, lote por lote, nesta ordem: ENEM → SSA → simulados ENEM → FUVEST/UNICAMP/UERJ/UNESP → demais → compilações.
5. Ao fim de cada sessão: atualizar o status no catálogo e a lista de pendências.
