# Banco MAPA — produto final e regras de extração

Atualizado em 27/09/2026. Referência: o banco de questões de uma mentoria de residência médica que o Matheus quer replicar para o vestibular.

## Como a questão aparece para o aluno

* Cabeçalho com etiquetas: etapa/fase, vestibular, ano e assunto. Botões para favoritar, anotar, ver informações e reportar erro.
* Texto de apoio em cima da questão quando ela cita um texto específico da prova ("Texto 7", "Textos 4 e 5"): no banco a questão aparece isolada, então o texto citado tem de vir junto para o aluno ler (pedido do Matheus, 26/09). Vale para qualquer prova, mas só para questões com essa citação; a maioria das questões não tem.
* Enunciado com imagens no lugar certo do texto.
* Fonte sempre antes do comando da questão (pedido do Matheus, 26/09): a fonte ("Disponível em…", "Fonte: …") aparece logo depois do texto ou da figura a que se refere e nunca depois da pergunta/comando. Vale para todas as questões.
* Equação química com a seta (pedido do Matheus, 27/09): a seta de reação desenhada no PDF vira o caractere da seta no texto (→, ←, ↔ ou ⇌ para equilíbrio), com a equação inteira numa linha só. Sem a seta, o aluno não reconhece que é uma reação.
* Alternativas separadas, cada uma podendo ser riscada.
* Depois de responder: um comentário curto em cada alternativa (✓/✗) e uma mensagem personalizada ("Você marcou A, mas o gabarito é C").

## Resolução (gerada depois, na fase de resolução)

Cada questão terá:

1. Comentário curto por alternativa: uma frase explicando por que está certa ou errada.
2. Alternativa correta: explicação em tópicos.
3. Alternativas incorretas: análise do erro de cada uma.
4. Quadro-resumo: tabela, opcional.
5. Armadilha: aba com título próprio para cada questão, opcional.
6. Leve para a prova: o recado final, em uma ou duas frases.
7. Passos do raciocínio: passo a passo numerado, direto e objetivo.

## REGRA DE OURO DA EXTRAÇÃO (decisão do Matheus)

A extração é uma cópia fiel. Nada da questão é inventado, acrescentado, resumido ou alterado.

* O texto é copiado exatamente como está no PDF.
* A imagem é recortada da página e inserida como está.
* NÃO escrever descrição de imagem nem qualquer outro conteúdo gerado.
* Se um trecho não puder ser copiado com certeza, a questão é marcada para revisão humana. Nunca se adivinha.

## Regras técnicas (a serviço da cópia fiel)

* Imagem = só a figura. Recortar apenas o gráfico/figura/mapa, em alta resolução. Nunca o print da questão inteira.
* Uma ilustração = um recorte só. Partes de uma mesma ilustração sem texto da questão entre elas viram UMA imagem que cobre tudo. Só se separa quando há texto do enunciado no meio ou quando cada parte é uma alternativa.
* Recorte nunca cortado: tabela, gráfico, foto e moldura saem inteiros. Texto girado (rótulo vertical de eixo) faz parte do gráfico.
* Texto da figura fica na figura (pedido do Matheus, 27/09): rótulos, unidades e títulos de eixo ("450 m", "Tempo (min)", "Calçada", "Círculo C₃") vão na imagem, mesmo quando encostam na borda ou ficam logo abaixo dela. Nunca viram texto solto no enunciado.
* Texto nunca vira imagem: alternativas, fontes ("Disponível em…") e fórmulas são texto (fórmulas em LaTeX). Se o PDF tem o texto desenhado, a questão fica PENDENTE até ser transcrita lendo a página.
* Marcadores de posição no enunciado: `{{img:N}}` onde a figura aparece e `{{fonte:N}}` onde a fonte N aparece (N = posição na lista `fontes`). O último parágrafo do enunciado é sempre o comando da questão: fontes (e figuras de layout lateral) que vinham depois dele sobem para antes dele.
* Tabelas: transcritas célula por célula quando for possível com certeza; se não, ficam como imagem recortada inteira.
* Formatação preservada: parágrafos, negrito, itálico e sublinhado (ex.: "CORRETO", "EXCETO"). Linha centralizada (equação, título) é parágrafo próprio.
* Alternativas estruturadas (letra + texto). Toda questão tem de sair com as 5 alternativas. Só é imagem quando a alternativa é de fato um desenho (gráfico, figura).
* Fonte/citação do texto (ex.: "Disponível em…", "Disponible en…", "Available at…") em campo separado (`fontes`), copiada exatamente, com a posição marcada no enunciado.
* Texto-base em entidade própria. Cada questão tem `textos_base_ids` (lista, na ordem) com todos os textos que ela usa: o texto ligado por "Texto para as questões X e Y" e os textos que ela cita pelo número. Em prova com opção de idioma, o número é procurado no texto do mesmo idioma.
* Resolução original do PDF, quando existir, copiada como está, em campo separado.
* Rastreio: arquivo e página de origem.
