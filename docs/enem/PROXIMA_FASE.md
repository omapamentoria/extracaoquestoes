# Próxima fase (aprovada pelo Matheus em 26/11): "fábrica" para o Drive inteiro (~2.900 PDFs)

Começa depois que as 5 sessões do ENEM 2020–2024 terminarem.

1. **Catálogo automático do Drive novo** (script, sem IA): listar tudo, separar prova / gabarito / resolução, ligar prova
   ao gabarito (nome, pasta e conteúdo: número de questões batendo), tirar arquivos repetidos.
2. **Extração em massa em segundo plano** (06_extrair.py, várias provas ao mesmo tempo, sem IA): gabarito conferido duas
   vezes, casamento com o banco (inclusive o antigo), verificação de prova inteira — tudo por script.
3. **Triagem por cor:** verde (completa, gabarito 100% oficial, sem alerta) vai direto para PR; amarelo (poucos símbolos
   desenhados/tabelas) resolvido em lote por tipo de problema; vermelho (escaneado, gabarito em formato novo, sem gabarito)
   vai para mutirão separado.
4. **Classificação barata:** sugestão automática pelo vizinho mais parecido entre as 26 mil questões já classificadas;
   modelo barato (Sonnet/Haiku) só confirma as incertas, em lotes; script confere área da prova e código da taxonomia.
5. **PR por lote grande** (instituição ou blocos de ~50 provas). No máximo 2–3 sessões ao mesmo tempo, por grupo.
6. Abrir uma sessão mestre nova com resumo curto (esta conversa ficou longa e cara).
