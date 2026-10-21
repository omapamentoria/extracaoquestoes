# Prompt para o Lovable: sincronização diária automática

Cole o texto abaixo no Lovable.

---

Quero que o banco de questões sincronize sozinho com o GitHub uma vez por dia. Antes de aplicar, me mostre um resumo do
que vai mudar.

1. Crie um agendamento no banco (pg_cron) que chame a função `public.trigger_question_sync()` **uma vez por dia, às
   10:00 UTC (07:00 de Brasília)**. Nome do agendamento: `sincronizar-banco-diario`. Não crie nenhum outro agendamento
   e não volte a ligar a rotina antiga de 15 minutos.
2. O agendamento só chama a sincronização que já existe (a mesma do botão "Sincronizar agora"). Ela já copia as
   imagens novas. Se num dia nada mudou no GitHub, ela termina com "0 criadas, 0 atualizadas".
3. Segurança: a função `question-bank-sync` aceita o cabeçalho `X-Mentor-Mode` com uma senha fixa escrita no código.
   Remova essa senha fixa. A função deve aceitar só o segredo da rotina (`X-Sync-Secret`, guardado em
   `question_sync_config`) ou um mentor logado. O botão "Sincronizar agora" continua funcionando para mentor logado.
4. Na tela de sincronização, mostre também "Próxima sincronização automática: amanhã às 07:00".
