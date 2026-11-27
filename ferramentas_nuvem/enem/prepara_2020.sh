#!/bin/bash
# ENEM 2020: depois da extracao (extrai.sh), monta o impresso (texto do amarelo, numero e gabarito da cor escaneada) e
# aplica os ajustes a mao. Sempre a partir da extracao original (os ajustes nao podem ser aplicados duas vezes).
cd /home/user/extracaoquestoes; E=ferramentas_nuvem/enem; M=$E/mapas
python3 $E/cor_por_texto.py P5400 P5420 $M/2020_d1_amarelo_para_branco.json $M/2020_d1_gabarito_branco.json
python3 $E/cor_por_texto.py P5402 P5421 $M/2020_d2_amarelo_para_azul.json $M/2020_d2_gabarito_azul.json
python3 $E/ajusta_extracao.py $E/correcoes/2020_extracao.json
