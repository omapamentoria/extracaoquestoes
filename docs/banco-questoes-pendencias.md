# Banco MAPA — lista de pendências

Atualizado em 28/09/2026. Para incluir um item, é só pedir ao Claude.

## Acervo: material para conseguir

* SSA 1, 2 e 3 de 2022, 2023 e 2024 (provas + gabaritos definitivos)
* SSA 3 de 2025
* Gabarito definitivo do SSA 2025 (etapas 1 e 2). Hoje está o preliminar
* FPS: provas + gabaritos (o Matheus vai conseguir o Drive)
* Confirmar se os gabaritos do SSA 2020 são definitivos
* ENEM 2015 (1ª aplicação), dias 1 e 2: os arquivos "Gabarito" são cópias da prova. Falta o gabarito oficial (há resolução comentada do Objetivo)
* ENEM 2009 (prova vazada): o gabarito do 2º dia é idêntico ao do 1º dia. Falta o gabarito certo do 2º dia
* ENEM 2020 impresso e ENEM 2025 (regular, 2ª aplicação e COP30): só há gabarito comentado, sem o gabarito oficial em PDF (dá para extrair do comentado)
* UFPR, UFG e UEG: pastas vazias (sem PDFs)
* No Google Drive (28/09/2026) não foram encontrados 3 arquivos de apoio do catálogo: `resolução famema 2026.pdf`, `BERNOULLI 0 2026 - DIA 02 B - GABARITO COMENTADO.pdf` e `2º SAS - resolução dia 02.pdf` (S4S 02 - 2026)

## Para o Matheus conferir

* Página "Revisão do Piloto MAPA": ENEM 2023 dia 2 e SSA 2025 1ª etapa dia 1 revisados e corrigidos (28/09/2026)
* Trechos transcritos pelo Claude lendo a imagem (o PDF não tem texto ali):
  * SSA 2025: Q34, Q37, Q38, Q40, Q44
  * ENEM 2023: Q158 (fórmula de V(x)), Q162 (o "*" dos caracteres especiais) e Q169 ("α =")
  * FUVEST 2017: Q49, 51, 58, 59, 80, 81, 82, 84–90
  * UNICAMP 2012: Q8, Q10, Q14, Q15
  * ENEM PPL 2012: Q104; Bernoulli 2019: Q124, Q149
* Páginas do Piloto 2, versão nova ("Piloto 2 ENEM e SSA", "Piloto 2 Simulados", "Piloto 2 FUVEST e UNICAMP"): conferir e mandar ao Claude o número das questões com erro
* Simulado SAS 2014: o "Segundo dia" do Simu 01 é o mesmo arquivo que o "Primeiro dia" do Simu 02. Um dos dois está trocado
* Simulado Bernoulli 2019 nº 01: o "Gabarito Primeiro dia" tem o conteúdo do caderno do 2º dia. O extrator agora detecta e usa o arquivo certo da mesma pasta
* Simulado SAS 2021 nº 01: não há arquivo de gabarito; desde 29/09 o gabarito vem da resolução comentada (94 de 95)
* Simulados Hexag UNESP 01 e 02: mesmo arquivo (já marcado como duplicata)
* Aba "Conferir" do `catalogo.xlsx`: 354 linhas com algum alerta (89 provas sem gabarito pareado, a maioria de UEL/UFU/UNEMAT; arquivos com texto ruim; gabaritos sem prova)

## Acervo: conferências do Claude

* Catálogo completo de todos os PDFs (26/09/2026): 4.237 PDFs, 1.834 a extrair, 494 duplicatas, 618 sem questões
* Detalhar FATEC, FAMERP, FAMEMA, UEL, UFGD, UFU, UFMS, UNEMAT, Unifesp (estão no catálogo, grupo DEMAIS)
* Marcar arquivos duplicados
* Textos que precisam de visão/OCR: 210 arquivos a extrair. Entre as provas prioritárias: ENEM 2010 1º dia, ENEM 2013 (2 dias), ENEM 2014 regular (2 dias) e 3ª aplicação, ENEM PPL 2014 e 2016, ENCCEJA 2017, Somos 2022, Bernoulli 2024 nº 05 e 06
* ENEM 2021 regular, dias 1 e 2 (P2586, P2589): o catálogo marca o texto como "ok", mas a camada de texto está embaralhada (fonte sem tradução). Vai para a etapa de visão/OCR. Os arquivos "comentado" (P2584, P2587) têm texto bom, com as resoluções misturadas
* ENEM 2010 1º dia: o texto está com as letras deslocadas (cifra simples). Dá para testar a decodificação, desde que cada questão seja conferida com a imagem da página
* Compilações e apostilas: deduplicar contra as provas oficiais na hora da extração (muitas repetem questões de ENEM/FUVEST)
* UEL: os cadernos de inglês e espanhol são a mesma prova, trocando só a língua estrangeira. Extrair um caderno completo e, do outro, só as questões de língua

## Proteções já no extrator (v138)

### Formato das provas

* O código descobre sozinho como a prova numera questões e alternativas (QUESTÃO 91, 10., número em caixa, a), (A), A., 4 ou 5 alternativas)
* Páginas de redação, rascunho, capa com ficha do candidato, códigos internos de simulado, logotipos repetidos, marca d'água girada na margem e texto escondido (camada oculta) ficam fora
* Gabarito lido de tabela horizontal, cartão de respostas desenhado, resolução comentada ou do arquivo certo da mesma pasta
* Símbolos gravados como imagem (fonte Type3 e "(cid:N)": hífen, ×, ≈, α, parênteses grandes) são reconhecidos por uma tabela de glifos conferida por visão; fórmula montada com eles fica PENDENTE para transcrição
* "Note e adote" e dados depois das alternativas ficam depois das alternativas

### Texto e fórmulas

* Alternativa nunca sai como foto de texto. Se o PDF tem o texto desenhado, a questão fica PENDENTE até ser transcrita (pasta `_banco/transcricoes`)
* Alternativas que são linhas de tabela viram texto (cabeçalho + linha)
* Fórmulas viram texto (LaTeX): frações, raízes, vetores, chapéu de ângulo, sistemas. Letras da fonte Symbol viram gregas (α, π...)
* Reações químicas mantêm a seta (→, ←, ↔, ⇌)
* Sublinhado é mantido (e não é confundido com barra de fração)
* Caractere duplicado no PDF (ex.: "··" em CaCl₂·2H₂O) é removido

### Imagens

* Uma ilustração = um recorte só: partes lado a lado ou empilhadas, setas, rótulos, legendas e títulos de eixo ficam juntos
* Figuras de alternativas diferentes nunca se juntam; alternativas desenhadas numa imagem só são recortadas uma por alternativa
* O texto da figura (unidades, rótulos, títulos) fica na figura, e o que é texto da questão sai da imagem
* Recorte nunca é cortado: tabela (inclusive a "aberta", sem moldura lateral) e foto entram inteiras
* Recorte que engoliria o texto ao lado não é feito (cada figura fica separada)
* Texto de fora que ficou dentro do recorte é pintado de branco, só se já estiver no texto da questão
* Moldura/tabela de layout em volta de texto não vira imagem; só a figura de dentro (desenho feito só de fios continua desenho)

### Estrutura da questão

* Fontes sempre antes do comando
* Questão que cita "Texto N" mostra esse texto em cima
* Cabeçalho "Questões de N a M" nunca entra numa questão
* Cada item vai para a questão cujo cabeçalho está acima dele na mesma coluna (provas antigas com divisória "——— 22")
* Figura no meio de uma frase vai para antes do enunciado, sem cortar o texto
* Parágrafos e versos respeitam o original (recuo, espaço, linha curta, centralização, assinatura, listas, itens I/II/III com recuo)
* Número de parágrafo fica como texto no começo do parágrafo

### Conferências automáticas

* Nenhum pedaço da página fica sem ser lido
* Trecho desenhado ou caractere que o PDF não traduz gera PENDENTE
* Alertas para alternativas idênticas, texto solto ao lado de imagem e recorte possivelmente cortado
* Teste de regressão (antes/depois) a cada mudança no código: ENEM 2023 e SSA 2025 não podem mudar

### Detalhes menores aceitos no Piloto 1

* SSA Q16 (meme): o recorte inclui a borda do quadro e um pedacinho de "ç"
* SSA Q12 (foto): pequena marca de letra no topo
* SSA Texto 9: "By" fica como parágrafo em negrito separado; os créditos dos autores ficam nas fontes
* SSA Q31: alerta "Compositor" é falso alarme

## Piloto 2: 2ª rodada (v138, 28/09/2026)

Corrigido com regras condicionais; ENEM 2023 e SSA 2025 sem nenhuma mudança:

* ENEM 2005: tabela inteira e em texto (Q4), alternativas em tabela (Q48), quadrinhos separados sem engolir o texto (Q25), gráfico não partido (Q38), marca d'água fora da figura (Q63), cabeçalho "2005" solto removido
* SSA 2018: capa "DADOS DE IDENTIFICAÇÃO DO CANDIDATO" fora do banco
* UNICAMP 2012: figura da cerca no texto-base (e não na Q8); as duas figuras de órbita no texto-base; Q8, Q10, Q14, Q15 digitadas (sistemas e raízes)
* FUVEST 2017: alternativas em tabela (Q52, Q54, Q71) em texto; heredogramas (Q49) e fórmulas (Q78) recortados um por alternativa; 14 questões transcritas; nenhuma PENDENTE
* ENEM PPL 2012: planificação do cubo (Q144) volta a ser imagem
* Bernoulli 2019: resto da resolução escondida removido; Q124 com os símbolos certos

Ainda abertos:

* ENEM PPL 2012 Q170: tabela "tempo t | altitude y" ainda sai como linhas soltas
* FUVEST Q52: lacunas "I" saem quebradas em linhas
* FUVEST: números de linha na margem dos textos literários (5, 10, 15…). Decidir: manter como marcador ou tirar
* Gabaritos só em imagem de cartão ou comentados sem número de questão: ler por visão quando o código não conseguir

## Fase 1 (ENEM), lote 1 (29/09/2026)

* Célula de tabela que fica fora do recorte (ENEM PPL 2023 Q176, "Matemática" da Tabela II) vira texto solto e depois é apagada da imagem pelo branqueamento: a imagem perde a célula. Sempre gera o alerta "texto curto solto junto da imagem" — conferir essas questões. Na Q176 as tabelas foram digitadas (transcrição)
* Transcritas por visão no lote 1: ENEM 2024 d2 Q106 (setas conferidas), Q139, Q150; ENEM 2022 d2 Q108, Q111, Q150, Q175; ENEM PPL 2023 d2 Q141, Q173, Q176

## Lista de OCR: repescagem e OCR (29/09/2026, extrator v139)

* Grupos das 159 provas "outras": `docs/lotes/outras_grupos.md`. 108 recuperadas (regras novas de cabeçalho: "QUESTÃO N" sem negrito, número grande solto da UERJ/USS, número + texto na mesma linha)
* OCR (tesseract, português): `ferramentas_nuvem/ocr_pdf.py` gera `~/mnt/BM/_ocr/<PID>.pdf`; o 06 lê esse arquivo quando ele existe. 22 provas recuperadas por OCR (9 das 46 de texto ruim + 13 de camada de texto inútil, lista em `docs/lotes/ocr_extra.txt`). Toda questão lida por OCR tem alerta
* As outras provas de OCR ficaram na lista por terem mais da metade das questões PENDENTES (alternativas não separadas) ou o número da questão em caixa preta (o OCR não lê): próximo passo é visão
* Discursivas: 40 das "outras" (UEL 2ª fase por disciplina, FAMERP dia 2, UERJ discursiva) entraram no formato discursivo, com alerta. As 23 discursivas de texto ruim ainda não passaram pelo OCR
* Página "Revisão de Alertas MAPA" (https://claude.ai/artifact/Qb2GDy8uJShaYgm5mchRfp): 3.231 questões com alerta das 117 provas recuperadas. As marcações ("certa"/"tem erro" + nota) ficam na coleção `revisao` do banco de dados da página (o Claude lê com ArtifactData). Gerada por `ferramentas_nuvem/rev_alertas.py`
* ENEM anteriores a 2005 (1998 a 2004: P2377, P2381, P2384, P2388, P2391, P2394, P2397): fora do banco por decisão do Matheus (muitos erros). Lista em `docs/lotes/fora_do_banco.txt`, respeitada pelo `lote.py`
* Arquivos que não são a prova: FATEC 2020_2/2021 (P0828), Famerp 2020 (P0760), unemat.pdf (P2037), ENEM 2007 (P2408): 1 página só

## Banco unificado — primeira carga (30/09/2026)

Plano completo em `docs/estrategia-banco-unificado.md`; diagnóstico da plataforma em `docs/plataforma/diagnostico.md`.

* **Primeira carga: 26.847 questões** = 5.288 antigas (2.912 com o texto novo, 2.376 como estavam) + 21.559 novas.
  Só entram objetivas prontas, sem alerta, com gabarito oficial (`unificacao/resumo.md`).
* Pares em dúvida decididos pelo Matheus (`unificacao/decisoes_matheus.json`). A antiga 620 (ENEM PPL 2020 Q135)
  ficou como **anulada**, porque o gabarito oficial do INEP anula a questão (o Matheus tinha marcado "fica a antiga").
* **17 questões antigas com comentário a refazer**: o gabarito do banco antigo estava errado; vale o oficial
  (ENEM PPL 2011, 2012, 2016, 2020, ENEM 2025 PPL e 11 do SSA). Lista: `motivo` "comentário a refazer" em
  `unificacao/pares.json`.
* Para o Matheus olhar: ENEM 2025 PPL dia 1, questão 12 (perfil epidemiológico). O gabarito oficial e o comentado
  dizem B; pela leitura, D parece mais lógica. Ficou B (oficial).

### Gabarito — auditoria (30/09/2026). Regra: só vale o gabarito oficial da mesma cor e do mesmo caderno da prova
* Corrigido no extrator: tabela com várias cores (ENEM 2009 dia 1: 22 gabaritos), gabarito comentado passando na
  frente do oficial (ENEM 2025: 554 gabaritos que faltavam + Q100 da reaplicação dia 2), gabarito de outra cor ou
  de outro caderno nunca é usado (cor e caderno lidos no catálogo, no nome do arquivo ou na capa da prova).
* Ferramentas: `ferramentas_nuvem/audita_gabarito.py` (recalcula todos os gabaritos com as regras atuais).
* **163 provas com gabarito só de resolução ficaram FORA da primeira carga** (`docs/lotes/gabarito_nao_confirmado.txt`):
  153 simulados ENEM (SAS, Bernoulli, Poliedro, SOMOS…), 5 outros simulados, FAMERP/FAMEMA dia 1 e ENEM 2020
  impresso dia 2. A leitura automática das resoluções já errou (SOMOS 2025; ENEM 2020 com o comentado em outra
  ordem de questões). **Próximo passo**: confirmar o gabarito de cada formato (SAS, Bernoulli, Poliedro, SOMOS)
  com leitura própria para o formato e conferência na imagem da página; o que for confirmado entra no banco.
  São cerca de 10 mil questões.
* ENEM 2020 impresso (dia 2): falta o gabarito oficial do INEP (o comentado do acervo é de outra cor).
* ENEM 2011 dias 1 e 2 (P2503, P2506): trechos cifrados sem alerta; fora das prontas (`docs/lotes/fora_das_prontas.txt`).
* SSA 2018: "NULA" no gabarito definitivo não é lido como anulada (a questão fica sem gabarito): ajustar.
* ENEM anteriores a 2005 fora do banco (decisão do Matheus): `docs/lotes/fora_do_banco.txt`.

## Resolução comentada pelo Gemini (30/09/2026)

* O ramo `comentarios-gemini` do Banco-de-questoes tem 719 lotes de 30 questões (21.551 no total), com as figuras.
  As instruções estão em `comentarios/INSTRUCOES.md`; o prompt e o passo a passo, em `docs/prompt-gemini.md`.
* Ficaram fora dos lotes: a 620 (anulada no oficial) e a 103369 (sem alternativas; conferir a extração).
* O conferidor é `ferramentas_nuvem/confere_comentarios.py`. A junção entra no `converte.py` (variável COMENTARIOS=).
* Os casos "discordo" e "sem_imagem" vão para a revisão do Matheus.

## Decisões em aberto

* ENCCEJA: incluir ou não? (metade é de ensino fundamental; no catálogo, prioridade 9 para médio e 10 para fundamental)
* Livros didáticos e apostilas (27.500 páginas): entram no banco ou ficam para depois?
* Taxonomia MAPA: disciplina → assunto → subassunto
* FUVEST: número de linha na margem do texto literário

## Próximas etapas

* ~~Piloto 1: ENEM 2023 dia 2 + SSA 2025 1ª etapa dia 1 (26/09/2026)~~
* ~~Corrigir o extrator com a revisão do Matheus e a autorrevisão do Claude (v136, 28/09/2026)~~
* ~~Piloto 2, 1ª rodada: 7 provas (ENEM 2005, ENEM PPL 2012, SSA 2018, Bernoulli 2019, SAS 2021, FUVEST 2017, UNICAMP 2012), v137 (28/09/2026)~~
* ~~Piloto 2, 2ª rodada: correções da revisão do Matheus + transcrições por visão (v138, 28/09/2026)~~
* ~~Migração para sessão Claude Code na nuvem (28/09/2026): arquivos via Google Drive, regressão das 9 provas-base conferida~~
* Revisão do Matheus da versão nova das 3 páginas do Piloto 2
* Escala na ordem: ENEM → SSA → simulados ENEM → FUVEST/UNICAMP/UERJ/UNESP → demais → compilações
* Classificação por assunto
* Resoluções comentadas (avaliar plano Max)
* Integração com a plataforma (Supabase/Lovable)
