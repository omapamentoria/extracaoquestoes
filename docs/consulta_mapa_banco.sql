-- Mapa do banco de questões para o Claude (somente leitura: não altera nada).
-- Devolve UMA linha com UM campo "mapa" (JSON) com tudo o que a Fase 1 precisa.
-- Dados dos alunos saem só como contagens (sem nomes, e-mails ou ids de aluno).
select json_build_object(
  'gerado_em', now(),
  'areas',       (select json_agg(x order by x.ordem) from public.areas x),
  'materias',    (select json_agg(x order by x.area_codigo, x.ordem) from public.materias x),
  'assuntos',    (select json_agg(x order by x.materia_codigo, x.ordem) from public.assuntos x),
  'subassuntos', (select json_agg(x order by x.assunto_codigo, x.ordem) from public.subassuntos x),
  'assuntos_prova', (select json_agg(x) from public.assuntos_prova x),
  'depara', (select json_agg(json_build_object('texto', texto_normalizado, 'area', area_correta,
                 'assunto', assunto_codigo, 'subassunto', subassunto_codigo, 'registros', registros))
             from public.depara_texto_livre),
  'questoes', (select json_agg(json_build_object('id', question_id, 'prova', prova, 'arquivo', arquivo_origem,
                 'ano', ano, 'numero', numero, 'area', area_codigo, 'materia', materia_codigo,
                 'assunto', assunto_codigo, 'subassunto', subassunto_codigo, 'assunto_nome', assunto_nome,
                 'subassunto_nome', subassunto_nome, 'status', status, 'nota', nota_revisao, 'imagem', tem_imagem))
               from public.questoes),
  'uso_por_questao', (select json_agg(json_build_object('id', question_id, 'respostas', n, 'acertos', a, 'alunos', u))
                      from (select question_id, count(*) n, count(*) filter (where acertou) a, count(distinct user_id) u
                            from public.question_attempts group by question_id) t),
  'relatos', (select json_agg(json_build_object('id', question_id, 'motivo', motivo, 'descricao', descricao,
                'status', status, 'data', created_at)) from public.question_reports),
  'questoes_em_listas', (select json_agg(distinct question_id) from public.question_session_items),
  'erros_simulado', (select json_agg(json_build_object('area', area_codigo, 'materia', materia_codigo,
                       'assunto', assunto_codigo, 'subassunto', subassunto_codigo, 'outro', assunto_outro, 'n', n))
                     from (select area_codigo, materia_codigo, assunto_codigo, subassunto_codigo, assunto_outro, count(*) n
                           from public.erros_simulado_questoes group by 1, 2, 3, 4, 5) t),
  'totais', json_build_object(
     'questoes', (select count(*) from public.questoes),
     'respostas', (select count(*) from public.question_attempts),
     'alunos_que_responderam', (select count(distinct user_id) from public.question_attempts),
     'listas', (select count(*) from public.question_sessions),
     'alunos_com_acesso', (select count(*) from public.question_bank_access where liberado),
     'relatos', (select count(*) from public.question_reports))
) as mapa;
