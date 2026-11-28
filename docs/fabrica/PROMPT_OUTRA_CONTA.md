# Prompt para continuar a fábrica em outra conta do Claude

## Antes de colar (o Matheus faz uma vez)

1. Na outra conta, abra claude.ai/code e ligue o GitHub (Configurações → Conectores → GitHub) com acesso aos
   repositórios `omapamentoria/extracaoquestoes` e `omapamentoria/Banco-de-questoes`.
2. Comece uma sessão nova com o repositório `omapamentoria/extracaoquestoes`, ramo `claude/fabrica-v2`.
3. Cole o texto abaixo (tudo entre as linhas).

---

Você vai continuar a "fábrica" do banco de questões MAPA, do Matheus (MAPA Mentoria). Ele é leigo em programação:
responda sempre em português do Brasil, em linguagem simples, com passo a passo e texto pronto para colar. Todo o
código e toda a execução ficam com você. Seja muito econômico em créditos: o trabalho pesado vai em scripts Python, em
segundo plano, e você nunca lê arquivos grandes nem provas inteiras.

**Leia antes de agir, nesta ordem:** `CLAUDE.md`; a seção 11 de `docs/HANDOFF-conta-mapa.md`;
`docs/fabrica/ESTRATEGIA_V2.md`; `docs/PENDENCIAS_BANCO.md`; `_banco/fabrica/enem2000a2008/relatorio.md` (exemplo
de um lote pronto).

**Onde estão as coisas**
- Ferramentas e catálogo: repositório `omapamentoria/extracaoquestoes`, ramo `claude/fabrica-v2` (trabalhe sempre a
  partir dele). Fábrica: `ferramentas_nuvem/fabrica/` (`roda_lote.py`, `mutirao.py`, `verifica_lote.py`,
  `gab_generico.py`). Ferramentas do ENEM: `ferramentas_nuvem/enem/`. Extrator: `_banco/codigo/06_extrair.py`.
- Catálogo do Drive novo: `_banco/catalogo_drive2/drive2_<instituicao>.json` (códigos P6000–P9885; o campo
  `drive_id` é o ID do arquivo no Drive). Resumo por instituição: `_banco/catalogo_drive2/resumo/`.
- Drive novo (pasta pública): https://drive.google.com/drive/folders/1XaHPSOkJqjAYt3CifEZ71jopiWGWEjT8. Baixe cada
  PDF pelo ID: `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t" -o arquivo.pdf`.
- Banco publicado: repositório `omapamentoria/Banco-de-questoes`, ramo padrão `claude/busy-tesla-cibdm3`, pasta
  `final/partes/` (cada parte é um JSON de uma linha só). Para trabalhar: clone raso e esparso
  (`git clone --depth 1 --filter=blob:none --sparse ...; git sparse-checkout set final`).
- Ids e partes já usados: as partes vão até a 36 e os ids até 180xxx. Para cada lote novo, use uma PARTE nova
  (37, 38, ...) e um ID_BASE novo (190000, 200000, ...), sem repetir.

**Regras de ouro (nunca quebre)**
1. Cópia fiel, nada inventado. O incerto não é publicado: fica marcado e explicado.
2. Gabarito só o oficial da própria prova (mesma cor ou caderno), conferido 100% pelo script e pelo conteúdo.
   Errar gabarito é erro grave. Se a conta da questão não bater com o oficial, pergunte ao Matheus antes de publicar.
3. Gabarito corrigido: o comentário da questão é apagado (os 8 campos vazios), a questão continua publicada e vai para
   a lista `final/comentarios_a_refazer_*.json`.
4. Mudança grande no banco (mais de 30 questões, mais de 10 gabaritos, ou alguma questão saindo da publicação): abra um
   PR para `claude/busy-tesla-cibdm3` e **não faça merge**. O Matheus aprova. Mudança pequena pode ir direto.
5. Questão que já está no banco mantém id, comentário e classificação (o `integra.py` casa pelo texto).

**Como trabalhar (o que já aprendemos)**
- O robô faz o grosso sem IA: `roda_lote.py` baixa, extrai, confere o gabarito, casa com o banco, sugere a
  classificação, separa as questões em prontas e pendentes, publica as prontas e verifica.
- As pendentes (figura, tabela, símbolo, alternativas, questão não extraída) vão para o mutirão (`mutirao.py`), em
  lotes pequenos do mesmo tipo, lendo só o recorte de cada questão.
- **A classificação automática erra muito:** no ENEM 2000–2008, 281 de 349 sugestões foram corrigidas. Toda
  classificação de confiança baixa tem que ser conferida antes do PR.
- **Sessões curtas:** um lote (até ~10 provas) por sessão, depois termine. Conversa longa é o que mais gasta.
  Para o mutirão e a classificação, use o modelo Sonnet. No máximo 2 sessões ao mesmo tempo.
- A prova só ganha os campos `prova_completa*` quando todas as questões dela estiverem prontas.
- Faça commit e push no `claude/fabrica-v2` a cada etapa. Atualize `docs/PENDENCIAS_BANCO.md` (o que falta) e a seção
  11 do HANDOFF (o que foi feito), em poucas linhas.

**Ordem do trabalho**
1. **ENEM 2000–2008, as 13 que faltam** (veja `_fora` em `ferramentas_nuvem/fabrica/correcoes/enem2000a2008.json`).
   Em 11, o extrator não achou o cabeçalho da questão; as outras 2 (ENEM 2006, página 19, questões 60 e 61) saíram
   com as colunas embaralhadas. Ensine o extrator a achar essas questões, ou transcreva as 13 lendo a página, com
   gabarito oficial. O PR #30 (as outras 554) já está no banco: abra um PR pequeno só com as 13.
2. **Provas verdes de medicina de São Paulo:** Unesp, Unifesp, Famerp, UNICAMP, Einstein, Santa Casa, Santa Marcelina,
   São Camilo, FACISB, FMJ, Fameca, Humanitas, FMABC, PUC-SP, PUC-Campinas. Um PR por instituição (ou por bloco de
   ~50 provas).
3. **Outras públicas grandes, só as verdes:** UECE, UFJF, UFU, UEA, UPE, UNEMAT, UEL, UFRGS e as demais.
4. **As amarelas**, por tipo de problema. **Por último, as vermelhas** (gabarito de somatória da UEM/UFSC/UEPG,
   certo/errado da UnB, escaneadas, sem gabarito) e as discursivas.

Antes de cada lote, diga ao Matheus, em 3 linhas, o que vai fazer. No fim de cada lote, responda com um resumo curto:
provas, questões publicadas, novas, pendentes, gabaritos corrigidos, custo aproximado e o link do PR.

---

## Regra nova de gabarito (aprovada pelo Matheus em 28/11; cole na outra conta depois do prompt)

```
Regra nova de gabarito (aprovada pelo Matheus): quando não houver gabarito oficial de uma questão, procure primeiro o oficial na internet (INEP ou a banca). Se não achar, aceite o gabarito de sites confiáveis (Descomplica e outros) só quando duas fontes diferentes concordarem e a resolução da questão confirmar; marque essas questões como "gabarito de fonte não oficial". Anote esta regra no CLAUDE.md.
```
