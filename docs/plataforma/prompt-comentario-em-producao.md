# Prompt para o Lovable: "Comentário em produção" e status dos avisos

Cole o texto abaixo no Lovable.

---

Preciso de dois ajustes no banco de questões. Antes de aplicar, me mostre um resumo do que vai mudar.

**1. Questão sem comentário mostra "Comentário em produção"**

Algumas questões tiveram o gabarito corrigido e o comentário antigo foi apagado, porque defendia a resposta errada. Elas
continuam publicadas, com o gabarito certo, e vão receber um comentário novo depois.

- Uma questão está "sem comentário" quando `explicacao_correta_texto` está vazio ou nulo **e** `passos_raciocinio` está vazio.
- Nesses casos, depois que o aluno responde, mostre no lugar da resolução um aviso discreto: **"Comentário em produção —
  a resolução desta questão está sendo refeita."** Continue mostrando se ele acertou ou errou e qual é o gabarito.
- Não esconda essas questões das listas nem dos simulados. Elas só não entram no filtro "só questões comentadas", se ele
  existir.
- Quando a sincronização trouxer o comentário novo, o aviso some sozinho (é só a regra acima).

**2. Status dos avisos vindo do GitHub**

Os arquivos de aviso em `reports/AAAA-MM/<question_id>_<report_id>.json`, no ramo padrão do repositório, agora podem voltar
atualizados com `status` ("aberto" ou "resolvido"), `observacao_interna` e `resolvido_em`.

- Na sincronização, leia esses arquivos e atualize o aviso correspondente (pelo `report_id`) com esses três campos.
  Só atualize, nunca crie nem apague avisos por esse caminho.
- Na tela de avisos do mentor/admin, mostre o status e a observação.
- Para o aluno que enviou o aviso, quando ficar "resolvido", mostre "Seu aviso foi analisado e a questão foi corrigida.
  Obrigado!". Não mostre a `observacao_interna` ao aluno.
