# Correcoes manuais dos avisos (conferidas no PDF) + comentarios a refazer. Roda depois do aplica.py.
import json,glob,sys
S=sys.argv[1]; OUT=S+"/saida/partes"; QF=S+"/saida/quarentena.json"
LOG=json.load(open(S+"/log_aplica.json")); quar=json.load(open(QF))
COM={"passos_raciocinio":[],"analise_correta_titulo":"","analise_correta_texto":"","analise_incorretas_intro":"","analise_incorretas":[],"quadro_resumo":[],"leve_para_prova":"","flashcards":[]}
SONETO=("Leia o soneto do poeta português Manuel Maria Barbosa du Bocage, para responder às questões de 13 a 16.\n\n"
"Olha, Marília, as flautas dos pastores,  \nQue bem que soam, como estão cadentes!  \nOlha o Tejo a sorrir-se! Olha: não sentes  \nOs Zéfiros<sup>1</sup> brincar por entre as flores?\n\n"
"Vê como ali, beijando-se, os Amores  \nIncitam nossos ósculos<sup>2</sup> ardentes!  \nEi-las de planta em planta as inocentes,  \nAs vagas borboletas de mil cores!\n\n"
"Naquele arbusto o rouxinol suspira;  \nOra nas folhas a abelhinha para.  \nOra nos ares, sussurrando, gira.\n\n"
"Que alegre campo! Que manhã tão clara!  \nMas ah!, tudo o que vês, se eu não te vira,  \nMais tristeza que a noite me causara.\n\n"
"(Manuel Maria Barbosa du Bocage. Poemas escolhidos, 1974.)\n\n<sup>1</sup> Zéfiro: vento que sopra do ocidente.  \n<sup>2</sup> ósculo: beijo.\n\n")
NAVIO=("Leia a notícia, divulgada em maio 2017, para responder às questões de números 35 a 36.\n\n**Navio autônomo e elétrico**\n\n"
"O primeiro navio autônomo — e, além disso, totalmente elétrico — já tem data marcada para começar a navegar. O Yara Birkeland (homenagem ao cientista norueguês Kristian Birkeland) deverá começar a operar na segunda metade de 2018, levando produtos da fábrica de fertilizantes da Yara, em Porsgrunn, até as cidades de Brevik e Larvik — todas na Noruega.\n\n"
"O navio elétrico e autônomo deverá substituir 100 caminhões que fazem 40 000 viagens por ano. Ele operará exclusivamente nessa rota, um trajeto de 12 milhas náuticas, pouco mais de 22 km. Com 70 metros de calado<sup>1</sup> e 4 500 toneladas de porte bruto, o navio autônomo poderá atingir até 18,5 km/h (10 nós), mas deverá operar em velocidade de cruzeiro de 11 km/h (6 nós).\n\n"
"Ele será impulsionado por dois mecanismos azimutais, em que o motor inteiro se movimenta para fazer o navio virar. Seu conjunto de baterias pode prover até 4 MWh.\n\n"
"A navegação autônoma se baseará em um extenso conjunto de sensores redundantes, incluindo câmeras no visível e no infravermelho, RADAR (Radio Detection And Ranging), LIDAR (Light Detection And Ranging) e AIS (Automatic Identification System), um sistema de monitoramento de curto alcance já utilizado em navios e serviços de tráfego de embarcações.\n\n"
"<https://tinyurl.com/yapk5b5f> Acesso em: 10.10.2018. Adaptado.\n\n<sup>1</sup> Calado – distância vertical entre a superfície da água e a parte mais baixa do navio naquele ponto.\n\n")
POEMA=("**Dois e dois: quatro**\n\nComo dois e dois são quatro  \nsei que a vida vale a pena  \nembora o pão seja caro  \ne a liberdade pequena\n\n"
"Como teus olhos são claros  \ne a tua pele, morena  \ncomo é azul o oceano  \ne a lagoa, serena\n\n"
"como um tempo de alegria  \npor trás do terror me acena  \ne a noite carrega o dia  \nno seu colo de açucena\n\n"
"— sei que dois e dois são quatro  \nsei que a vida vale a pena  \nmesmo que o pão seja caro  \ne a liberdade, pequena.\n\n{{fonte:1}}\n\n"
"O poema, escrito originalmente em 1966, cita duas vezes a palavra “liberdade”. Diante do contexto em que foi produzido, tal palavra remete ao(à)")
QUAR={102076:"cópia da questão oficial 100140 (ENEM PPL 2009) dentro do simulado SAS",
}
confuso=set(json.load(open(S+"/coment_confuso.json")))|{115887,116390}
n=0
for f in sorted(glob.glob(OUT+"/*.json")):
    L=json.load(open(f)); fica=[]
    for q in L:
        i=q["id"]
        if i in QUAR: quar.append({**q,"_motivo_quarentena":QUAR[i]}); LOG.append((i,"quarentena",QUAR[i])); continue
        if i in (120217,120218,120219,120220): q["statement"]=SONETO+q["statement"]; LOG.append((i,"texto","soneto (texto-base das questões 13 a 16) incluído"))
        if i in (115130,115131): q["statement"]=NAVIO+q["statement"]; LOG.append((i,"texto","notícia do navio (texto-base das questões 35 e 36) incluída"))
        if i==106182: q["statement"]=POEMA; q["imagens"]=[]; q["tem_imagem"]="nao"; LOG.append((i,"texto","poema completo, na ordem do original"))
        if i==101649:
            q["statement"]=q["statement"].replace("\n\nCinto 1 Cinto 2 Cinto 3 Cinto 4 Cinto 5",""); LOG.append((i,"imagem","gráfico recortado de novo, com a legenda dos cintos"))
        if i==101640:
            q["statement"]=q["statement"].replace("**Figura 1**","{{img:1}}",1); q["imagens"]=["101640_1.webp"]; q["tem_imagem"]="sim"; LOG.append((i,"imagem","Figuras 1 e 2 (climograma e mapa) incluídas"))
        if i in confuso and q["passos_raciocinio"]:
            q.update(json.loads(json.dumps(COM))); LOG.append((i,"comentário","comentário confuso ou com erro removido para refazer")); n+=1
        fica.append(q)
    json.dump(fica,open(f,"w",encoding="utf-8"),ensure_ascii=False,indent=0)
json.dump(quar,open(QF,"w",encoding="utf-8"),ensure_ascii=False,indent=0); json.dump(LOG,open(S+"/log_aplica.json","w"),ensure_ascii=False)
print("comentarios removidos",n,"quarentena",len(quar))
