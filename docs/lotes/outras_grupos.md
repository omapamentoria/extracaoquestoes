# Provas "outras" da lista de OCR: grupos por tipo de problema

159 provas que não eram de texto ruim (29/09/2026). Recuperadas agora: **95**; ainda na lista: **64**.
Extrator v139 (regras condicionais; regressão das 9 provas-base sem nenhuma mudança). Rodado com `python3 ferramentas_nuvem/refaz_lista.py` (e `refaz_lista.py ocr` para o 1º grupo).

## Camada de texto inútil (página sem texto, OCR embutido ruim, fonte renumerada, questão como imagem)

23 provas; recuperadas 0. Tratadas como texto ruim: OCR do tesseract (`ocr_pdf.py`) e extração no modo OCR, com alerta em toda questão.

* ✘ P2463 — ENEM 2021 — enem 2021 PPL - 2 dia PROVA.pdf
* ✘ P2460 — ENEM 2021 — enem 2021 PPL - 1 dia PROVA.pdf
* ✘ P2421 — ENEM 2010 — ENEM PPL - 2010 (2°apli) - 1° dia - Prova azul.pdf
* ✘ P2863 — ENEM 2026 — 3° SOMOS - 2026 - Dia 02.pdf
* ✘ P3504 — ENEM 2025 — 2º Simulado SAS Enem 2025- prova 2º Dia.pdf
* ✘ P3498 — ENEM 2025 — 1º SAS 2025 - D2 .pdf
* ✘ P3497 — ENEM 2025 — 1º SAS 2025 - D1.pdf
* ✘ P2976 — ENEM 2025 — 1º SOMOS 2025 - D2.pdf
* ✘ P3489 — ENEM 2024 — 5º SAS 2024 - prova d2 - @wagnernamed.pdf.pdf
* ✘ P3488 — ENEM 2024 — 5º SAS 2024 - prova d1 - @wagnernamed.pdf.pdf
* ✘ P3484 — ENEM 2024 — 4º  SAS 2024 - prova d1 - @wagnernamed.pdf
* ✘ P3081 — ENEM 2024 — 2º Poliedro 2024 - prova d2 - @wagnernamed.pdf
* ✘ P3466 — ENEM 2023 — Prova - Dia 02- SAS 06_2023.pdf
* ✘ P3451 — ENEM 2023 — 3 SAS_2023  - DIA 1.pdf
* ✘ P3448 — ENEM 2023 — Dia 2 - sas 2_2023.pdf.pdf
* ✘ P3447 — ENEM 2023 — Dia 1 - sas 2_2023.pdf
* ✘ P3446 — ENEM 2023 — 1 SAS 2023 - DIA 2 PROVA.pdf
* ✘ P3444 — ENEM 2023 — 1 SAS 2023 - DIA 1 PROVA.pdf
* ✘ P1135 — FUVEST 2026 — fuvest 2026 - 1 fase prova V1.pdf
* ✘ P1099 — FUVEST 2014 — FUVEST 2014 - 1a fase - PROVA.pdf
* ✘ P2423 — ENEM 2010 — ENEM PPL - 2010 (2°apli) - 2° dia - Prova azul.pdf
* ✘ P2489 — ENEM 2009 — ENEM - 2009 (F) - 2°dia - Prova amarela.pdf
* ✘ P2487 — ENEM 2009 — ENEM - 2009 (F) - 1°dia - Prova amarela.pdf

## Arquivo que não é a prova (1 página, capa, planner, só redação)

4 provas; recuperadas 0. Não há o que extrair: conseguir o arquivo certo.

* ✘ P0828 — FATEC 2020 — FATEC 2020_2, 2021_1 E 2021_2.pdf
* ✘ P0760 — FAMERP 2020 — Famerp 2020.pdf
* ✘ P2037 — UNEMAT 2017 — unemat.pdf
* ✘ P2408 — ENEM 2007 — ENEM - 2007 - Prova amarela(1).pdf

## Prova discursiva com expectativa de resposta (UEL 2ª fase por disciplina, FAMERP dia 2, UERJ discursiva)

46 provas; recuperadas 40. O extrator já reconhece o formato discursivo; entram com alerta (discursivas ficam para a fase delas).

* ✘ P1306 — UEL 2026 — sociologia 2026.PDF
* ✔ P1304 — UEL 2026 — quimica 2026.PDF
* ✔ P1303 — UEL 2026 — lingua portuguesa e literatura 2026.PDF
* ✔ P1302 — UEL 2026 — historia 2026.PDF
* ✔ P1301 — UEL 2026 — fisica 2026.PDF
* ✔ P1300 — UEL 2026 — filosofia 2026.PDF
* ✔ P1299 — UEL 2026 — biologia 2026.PDF
* ✔ P1298 — UEL 2026 — artes 2026.PDF
* ✔ P1297 — UEL 2026 — Matemática 2026.PDF
* ✘ P0783 — FAMERP 2026 — famerp 2026- dia 02 prova.pdf
* ✔ P1288 — UEL 2025 — sociologia 2025.PDF
* ✔ P1285 — UEL 2025 — lingua portuguesa e literatura 2025.PDF
* ✔ P1284 — UEL 2025 — historia 2025.PDF
* ✔ P1283 — UEL 2025 — fisica 2025.PDF
* ✔ P1282 — UEL 2025 — filosofia 2025.PDF
* ✔ P1281 — UEL 2025 — biologia 2025.PDF
* ✔ P1280 — UEL 2025 — arte 2025.PDF
* ✔ P1279 — UEL 2025 — Matemática 2025.PDF
* ✘ P0779 — FAMERP 2025 — famerp 2025- dia 02 prova.pdf
* ✔ P1276 — UEL 2024 — sociologia 2024.PDF
* ✔ P1274 — UEL 2024 — quimica 2024.PDF
* ✔ P1273 — UEL 2024 — matematica 2024.PDF
* ✔ P1272 — UEL 2024 — lingua portuguesa e literatura 2024.PDF
* ✔ P1271 — UEL 2024 — historia 2024.PDF
* ✔ P1270 — UEL 2024 — fisica 2024.PDF
* ✔ P1269 — UEL 2024 — filosofia 2024.PDF
* ✔ P1267 — UEL 2024 — arte 2024.PDF
* ✘ P0775 — FAMERP 2024 — famerp 2024 - dia 02 prova.pdf
* ✔ P1264 — UEL 2023 — sociologia 2023.PDF
* ✔ P1263 — UEL 2023 — quimica 2023.PDF
* ✔ P1262 — UEL 2023 — matematica 2023.PDF
* ✔ P1261 — UEL 2023 — lingua portuguesa e literatura 2023.PDF
* ✔ P1260 — UEL 2023 — historia 2023.PDF
* ✔ P1259 — UEL 2023 — fisica 2023.PDF
* ✔ P1258 — UEL 2023 — filosofia 2023.PDF
* ✔ P1257 — UEL 2023 — biologia 2023.PDF
* ✔ P1256 — UEL 2023 — arte 2023.PDF
* ✘ P0771 — FAMERP 2023 — famerp 2023 - dia 02 prova.pdf
* ✘ P0768 — FAMERP 2022 — Prova 2.pdf
* ✔ P1248 — UEL 2020 — quimica 2020.PDF
* ✔ P1247 — UEL 2020 — matematica 2020.PDF
* ✔ P1246 — UEL 2020 — lingua portuguesa e literatura 2020.PDF
* ✔ P1245 — UEL 2020 — historia 2020.PDF
* ✔ P1244 — UEL 2020 — fisica 2020.PDF
* ✔ P1243 — UEL 2020 — filosofia 2020.PDF
* ✔ P1241 — UEL 2020 — arte 2020.PDF

## Cabeçalho "QUESTÃO N" sem negrito (FATEC, UFU, simulado UNESP, ENEM digital 2020, ENEM 2006)

28 provas; recuperadas 26. Regra nova `questao_nb` (vence só se a sequência for maior que a dos outros estilos); "Questão 92 - Ciências…" vira área.

* ✔ P2078 — UNESP  — Simulado Unesp primeira fase.pdf
* ✔ P0839 — FATEC 2024 — prova-fatec-vestibular-2024-2.pdf
* ✔ P0836 — FATEC 2024 — caderno-de-prova-fatec-2024.pdf
* ✔ P0833 — FATEC 2023 — fatec2023_2_prova.pdf
* ✔ P0827 — FATEC 2020 — FATEC 2020_1.pdf
* ✔ P0825 — FATEC 2019 — FATEC 2019_2.pdf
* ✔ P0823 — FATEC 2019 — FATEC 2019_1.pdf
* ✔ P1838 — UFU 2018 — UFU 2018 2º Dia 1º Fase.pdf
* ✔ P1836 — UFU 2018 — UFU 2018 1º Dia 1º Fase.pdf
* ✔ P0821 — FATEC 2018 — FATEC 2018_2.pdf
* ✔ P0819 — FATEC 2018 — FATEC 2018_1.pdf
* ✔ P0816 — FATEC 2017 — FATEC 2017_2 .pdf
* ✔ P0815 — FATEC 2017 — FATEC 2017_1.pdf
* ✔ P0813 — FATEC 2016 — FATEC 2016_2.pdf
* ✔ P0811 — FATEC 2016 — FATEC 2016_1.pdf
* ✔ P0809 — FATEC 2015 — FATEC 2015_2.pdf
* ✔ P0807 — FATEC 2015 — FATEC 2015_1.pdf
* ✔ P0805 — FATEC 2014 — FATEC 2014_2.pdf
* ✔ P0803 — FATEC 2014 — FATEC 2014_1.pdf
* ✔ P0801 — FATEC 2013 — FATEC 2013_2.pdf
* ✔ P0799 — FATEC 2013 — FATEC 2013_1.pdf
* ✔ P0797 — FATEC 2012 — FATEC 2012_2.pdf
* ✔ P0795 — FATEC 2012 — FATEC 2012_1.pdf
* ✔ P0793 — FATEC 2011 — FATEC 2011_2.pdf
* ✘ P0789 — FATEC 2010 — FATEC 2010_2.pdf
* ✔ P2579 — ENEM 2020 — enem2020_digital_2dia_prova_amarelo.pdf
* ✔ P2576 — ENEM 2020 — enem2020_digital_1dia_prova_amarelo.pdf
* ✘ P2403 — ENEM 2006 — ENEM - 2006 - Prova amarela.pdf

## Número grande solto, com rótulo "Questão" (UERJ, USS, simulados UERJ, FUVEST 2022)

28 provas; recuperadas 17. Regra nova `grande`; dígitos separados pela fonte ("0 1") são juntados; o rótulo "Questão" sai da linha.

* ✔ P1636 — UERJ 2025 — 1º exame qualificação 2025.pdf
* ✔ P1632 — UERJ 2024 — 2o_EQ 2024.pdf
* ✔ P1628 — UERJ 2024 — 1º exame prova.pdf
* ✔ P1624 — UERJ 2023 — prova_vetibular_2023.pdf
* ✘ P1618 — UERJ 2022 — UERJ - prova_2022.pdf
* ✘ P1123 — FUVEST 2022 — FUVEST 2022 - 1a fase - PROVA.pdf
* ✘ P1616 — UERJ 2021 — UERJ 2021 - prova.pdf
* ✘ P1612 — UERJ 2020 — UERJ 2020 - Segundo Exame.pdf
* ✘ P1610 — UERJ 2020 — UERJ 2020 .pdf
* ✔ P1606 — UERJ 2019 — UERJ 2019 - prova 2º Exame de Qualificação.pdf
* ✔ P1604 — UERJ 2019 — UERJ 2019 - prova 1º qualificação.pdf
* ✔ P1599 — UERJ 2018 — 2º Exame Qualificação 2018.pdf
* ✔ P1598 — UERJ 2018 — 1º Exame Qualificação 2018.pdf
* ✘ P1595 — UERJ 2017 — 2º Exame Qualificação 2017.pdf
* ✘ P1594 — UERJ 2017 — 1º Exame Qualificação 2017.pdf
* ✔ P1591 — UERJ 2016 — 2º Exame Qualificação 2016.pdf
* ✔ P1590 — UERJ 2016 — 1º Exame Qualificação 2016.pdf
* ✘ P1587 — UERJ 2015 — 2º Exame Qualificação 2015.pdf
* ✘ P1586 — UERJ 2015 — 1º Exame Qualificação 2015.pdf
* ✘ P1374 — UERJ  — simulado uerj.pdf
* ✔ P1372 — UERJ  — UERJ 2 SIMULADO.pdf
* ✘ P1370 — UERJ  — Simulado UERJ.pdf
* ✔ P1341 — USS 2021 — 2021.1 - USS - PROVA.pdf
* ✔ P1339 — USS 2021 — 2021-2 - USS - PROVA.pdf
* ✔ P1337 — USS 2020 — 2020.1 - USS - PROVA.pdf
* ✔ P1336 — USS 2020 — 2020.1 - 2 ED - USS - PROVA.pdf
* ✔ P1334 — USS 2019 — 2019.2 - USS - PROVA.pdf
* ✔ P1332 — USS 2019 — 2019.1 - USS - PROVA.pdf

## Número + texto na mesma linha, sem ponto (FUVEST 2010–2018, UFGD PSV, ENEM 1998–2004, UEL tipo 1, UNEMAT)

28 provas; recuperadas 12. Regra nova `lead`: número em negrito ou maior que o texto, seguido do texto.

* ✘ P1224 — FUVEST 2024 — Simulado Fuvest.pdf
* ✘ P1111 — FUVEST 2018 — FUVEST 2018 - 1a fase - PROVA.pdf
* ✔ P1105 — FUVEST 2016 — FUVEST 2016 - 1a fase -PROVA.pdf
* ✘ P1101 — FUVEST 2015 — FUVEST 2015 - 1a fase - PROVA.pdf
* ✔ P1096 — FUVEST 2013 — FUVEST 2013 - 1a fase - PROVA.pdf
* ✔ P1093 — FUVEST 2012 — FUVEST 2012 - 1a fase - PROVA.pdf
* ✔ P1090 — FUVEST 2011 — FUVEST 2011- 1a fase - PROVA.pdf
* ✔ P1087 — FUVEST 2010 — FUVEST 2010 - 1a fase - PROVA.pdf
* ✘ P1294 — UEL 2026 — prova-tipo-1-ingles-uel-2026-dia-1.PDF
* ✘ P1293 — UEL 2026 — prova-espanhol-uel-2026-dia-1.PDF
* ✘ P1278 — UEL 2025 — prova tipo 1 - 2025.PDF
* ✘ P1266 — UEL 2024 — prova tipo 1 - 2024.PDF
* ✘ P1255 — UEL 2023 — prova tipo 1 - 2023.PDF
* ✘ P1253 — UEL 2022 — prova tipo 1 - 2022.PDF
* ✘ P1251 — UEL 2021 — prova tipo 1 - 2021.PDF
* ✘ P1719 — UFGD 2020 — PSV-2020_Prova_Reda‡ֶo.pdf
* ✘ P1239 — UEL 2020 — prova tipo 1 - 2020.PDF
* ✔ P1710 — UFGD 2017 — UFGD 2017 PROVA.pdf
* ✘ P1707 — UFGD 2016 — PSV2016_TIPOA.pdf
* ✘ P1702 — UFGD 2015 — Prova_PSV_2015_Tipo_A.pdf
* ✘ P1981 — UNEMAT 2014 — provas unemat 2014 -  2023.pdf
* ✔ P1699 — UFGD 2014 — Prova_Objetiva_PSV-2014.pdf
* ✔ P1983 — UNEMAT 2006 — caderno_2_2006_1.pdf
* ✔ P1982 — UNEMAT 2006 — caderno_1_2006_1.pdf
* ✘ P2397 — ENEM 2004 — ENEM - 2004 - Prova amarela.pdf
* ✔ P2388 — ENEM 2001 — ENEM - 2001 - Prova amarela.pdf
* ✔ P2381 — ENEM 1999 — ENEM - 1999 - Prova amarela.pdf
* ✔ P2377 — ENEM 1998 — ENEM - 1998 -  Prova amarela.pdf

## Outros

2 provas; recuperadas 0. Ver caso a caso.

* ✘ P2242 — UNICAMP 2023 — unicamp2023_1fase_vs2.pdf
* ✘ P4142 — SSA 2016 — PROVA_SSA2_2DIA.pdf
