# ENEM completo: manual de uma sessão que extrai UM ano

Você é uma das sessões paralelas que extraem o ENEM por ano. A sessão mestre (a do Matheus, que criou você)
acompanha todas. Responda sempre em português do Brasil, em linguagem simples. Leia antes: `CLAUDE.md` e a seção 11 do
`docs/HANDOFF-conta-mapa.md`. O ENEM 2025 já foi feito com este mesmo método (PR #21 do `Banco-de-questoes`).

## O objetivo

Para o seu ano, TODAS as aplicações que existem no Drive novo (regular, PPL/reaplicação, digital, 2ª/3ª aplicação...):
- cada prova (cada dia) inteira no banco: 90 questões (no dia de Linguagens, mais as 5 do outro idioma: 95);
- uma cor por prova, com o gabarito oficial **dessa cor** (relido do PDF do INEP, 100% igual);
- cada questão com área, matéria, assunto e subassunto (taxonomia `unificacao/classif/taxonomia.txt`);
- sem duplicadas: questão que já está no banco (inclusive no banco antigo, ids < 10000) mantém o id e o comentário.

Regras de ouro: cópia fiel, nada inventado; gabarito só o oficial da própria prova (mesma cor); o incerto não é
publicado, fica marcado e explicado. Gabarito antigo diferente do oficial: vale o oficial, o comentário é apagado e a
questão vai para a lista a refazer (o `publica.py` faz isso sozinho).

## Seus parâmetros (não use outros: evitam conflito com as outras sessões)

| Ano | ID_BASE (ids novos) | PARTE (arquivo novo) | Códigos de PDF | REFAZER |
|---|---|---|---|---|
| 2024 | 130000 | 29 | P5000–P5099 | comentarios_a_refazer_2026-11_enem2024.json |
| 2023 | 135000 | 30 | P5100–P5199 | comentarios_a_refazer_2026-11_enem2023.json |
| 2022 | 140000 | 31 | P5200–P5299 | comentarios_a_refazer_2026-11_enem2022.json |
| 2021 | 145000 | 32 | P5300–P5399 | comentarios_a_refazer_2026-11_enem2021.json |
| 2020 | 150000 | 33 | P5400–P5499 | comentarios_a_refazer_2026-11_enem2020.json |

Ramos: no `extracaoquestoes`, `claude/enem-<ano>` (a partir de `claude/relaxed-brown-a22e9w`); no `Banco-de-questoes`,
`claude/enem-<ano>-completo` (a partir do ramo padrão `claude/busy-tesla-cibdm3`, sempre o mais novo).
**Nunca** grave no `_banco/catalogo_debug.json`, no HANDOFF nem nos ramos das outras sessões.

## Preparação (uma vez)

```bash
pip install -q opencv-python-headless pdfplumber
mkdir -p ~/mnt && ln -sfn /home/user/extracaoquestoes ~/mnt/BM
W=<scratchpad>/drive2; mkdir -p $W/pdf
ln -sfn $W/pdf "/home/user/extracaoquestoes/DRIVE NOVO"
```
Repositório do banco: `add_repo omapamentoria/Banco-de-questoes` (push), clone raso com sparse checkout de `final`,
`reports`, `docs` (`git clone --depth 1 --filter=blob:none --sparse ...; git sparse-checkout set final reports docs`).

Baixar os PDFs do seu ano, **um por um pelo ID** (há nomes repetidos no Drive, ex.: 2024 PPL), para
`$W/pdf/Públicas/ENEM/<ano>/...`: lista em `docs/enem/drive2_enem.json` (`{"id","path"}`);
`curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t" -o <arquivo>`.
Confira com `pdfinfo` e abra a 1ª página (`pdftotext -l 1`) para saber dia, cor e aplicação de verdade (o nome do
arquivo pode mentir). Arquivo de gabarito com nome repetido: salve com sufixo e descubra pelo conteúdo qual dia/cor é.

## Passo a passo

1. **Catálogo:** crie `_banco/catalogo_drive2/<ano>.json` (lista JSON) com uma entrada por PDF (prova e gabarito),
   copiando o formato das entradas P4238–P4249 do `_banco/catalogo_debug.json`. Campos que importam: `id`, `vestibular`
   "ENEM", `grupo` "ENEM", `ano`, `edicao` ("regular", "PPL/reaplicação", "digital", "2ª aplicação"... use o mesmo texto que
   as questões desse ano já usam no banco: veja `edicao` nas partes), `dia`, `caderno` (cor), `papel` ("prova"/"gabarito"),
   `gabarito_ids` (na prova: o código do gabarito da MESMA cor), `caminho` ("DRIVE NOVO/Públicas/ENEM/<ano>/<arquivo>"),
   `arquivo`, `status` ("a extrair" na prova), `origem` "DRIVE2". Escolha UMA cor por prova (prefira Azul; se só há uma, essa).
2. **Extrair e conferir o gabarito:** `ferramentas_nuvem/enem/extrai.sh <PIDs das provas>` (rode em segundo plano). Tem que
   dar `divergencias 0` em todas. Se não der, investigue (cor errada? gabarito de outro dia?) e não siga sem resolver.
3. **Pendências do extrator:** veja os `alertas` das questões (`_banco/questoes/ENEM/<ano>/<PID>/questoes.json`).
   - "PENDENTE" (símbolo desenhado, `(cid:`), caracteres estranhos (U+E000–U+F8FF): recorte a região da página com
     `pdftoppm` (use `paginas` e `caixas` da questão), leia a imagem e escreva a correção em
     `ferramentas_nuvem/enem/correcoes/<ano>.json` (formato igual a `correcoes/2025b.json`: `statement_sub` com regex e texto
     literal, `alt_sub`, `alternativas`; sempre com `motivo`). Fórmula: KaTeX entre `\( \)`.
   - Área errada (todas com a mesma área, ex.: Humanas lidas como Linguagens): `"_area": {"<PID>": [[46, 90, "CIÊNCIAS HUMANAS E SUAS TECNOLOGIAS"]]}`.
   - "tabela transcrita automaticamente": confira umas duas com a imagem.
4. **Casar com o banco:** para cada prova,
   `python3 ferramentas_nuvem/enem/integra.py <banco>/final/partes _banco/questoes/ENEM/<ano>/<PID> <scratch>/int_<PID>.json ferramentas_nuvem/enem/correcoes/<ano>.json`
   Leia o resumo: "gabarito diferente do banco" (vai virar correção pelo oficial — confira se é mesmo a mesma questão),
   "semelhança < 0.97" (olhe), e no fim confira que nenhuma questão do banco antigo do seu ano ficou sem par (script
   de exemplo: o trecho "antigas de 2025 sem par" no histórico do 2025; adapte o ano).
5. **Gravar:** num ramo novo do banco a partir do ramo padrão atualizado:
   `ID_BASE=... PARTE=... REFAZER=... python3 ferramentas_nuvem/enem/publica.py <banco> ferramentas_nuvem/enem/correcoes/<ano>.json <scratch>/int_*.json`
   (todas as provas do ano numa chamada só).
6. **Classificar** as questões novas (as do arquivo `banco_parte_<PARTE>.json`): liste-as de forma compacta (fim do
   enunciado + começo das alternativas), escolha o subassunto pela taxonomia (o conhecimento cobrado, não o tema do
   texto; língua estrangeira vai para Inglês/Espanhol; a área tem que ser a da prova) e grave em
   `ferramentas_nuvem/enem/classif/<ano>.txt` ("id subassunto" por linha). Depois:
   `python3 ferramentas_nuvem/enem/grava_classif.py <banco>/final/partes/banco_parte_<PARTE>.json ferramentas_nuvem/enem/classif/<ano>.txt 0`
   Confira também se alguma questão antiga casada tem área diferente da área da prova e corrija.
7. **Verificar:** `python3 ferramentas_nuvem/enem/verifica.py <banco> <PIDs>`: todas "OK". Nada vai para PR com FALHA.
8. **PR:** `git add --sparse final imagens`, commit em português (com as linhas de atribuição que o sistema der), push do
   ramo `claude/enem-<ano>-completo`, PR para `claude/busy-tesla-cibdm3` com a tabela por prova (cor, questões, do banco
   antigo, já existentes, novas, gabarito = oficial, gabaritos corrigidos, comentários a refazer). **Não faça merge.**
   Push do seu ramo `claude/enem-<ano>` do extracaoquestoes (catálogo do ano, correções, classificação, extração em
   `_banco/questoes/ENEM/<ano>/P5xxx` com `git add -f _banco/questoes/ENEM/<ano>/P5xxx/{questoes.json,textos_base.json,img}` — nunca a pasta `revisao`).
9. **Conflito:** se o ramo padrão mudar (outra sessão teve o PR aprovado) e o seu PR ficar com conflito, NÃO resolva na
   mão: crie o ramo de novo a partir do padrão mais novo e rode de novo os passos 4–7 (é rápido e dá o mesmo resultado;
   os ids das suas questões novas se mantêm). Use um nome de ramo novo (`-v2`) e abra outro PR, citando o anterior.
10. **Relatório:** escreva `docs/enem/<ano>.md` no seu ramo do extracaoquestoes: provas, cores, números, correções à mão
    (com o motivo), pendências. Termine respondendo com um resumo curto (o que foi feito, link do PR, o que ficou pendente).

Seja econômico: trabalho pesado em scripts, extração em segundo plano, não leia arquivos grandes inteiros.
