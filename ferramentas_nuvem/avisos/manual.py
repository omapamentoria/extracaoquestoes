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
POEMA=("**Dois e dois: quatro**\n\nComo dois e dois são quatro  \nsei que a vida vale a pena  \nembora o pão seja caro  \ne a liberdade pequena\n\n"
"Como teus olhos são claros  \ne a tua pele, morena  \ncomo é azul o oceano  \ne a lagoa, serena\n\n"
"como um tempo de alegria  \npor trás do terror me acena  \ne a noite carrega o dia  \nno seu colo de açucena\n\n"
"— sei que dois e dois são quatro  \nsei que a vida vale a pena  \nmesmo que o pão seja caro  \ne a liberdade, pequena.\n\n{{fonte:1}}\n\n"
"O poema, escrito originalmente em 1966, cita duas vezes a palavra “liberdade”. Diante do contexto em que foi produzido, tal palavra remete ao(à)")
QUAR={102076:"cópia da questão oficial 100140 (ENEM PPL 2009) dentro do simulado SAS",
      115130:"falta o texto-base compartilhado (notícia do navio autônomo)",115131:"falta o texto-base compartilhado (notícia do navio autônomo)"}
confuso=set(json.load(open(S+"/coment_confuso.json")))|{115887,116390}
n=0
for f in sorted(glob.glob(OUT+"/*.json")):
    L=json.load(open(f)); fica=[]
    for q in L:
        i=q["id"]
        if i in QUAR: quar.append({**q,"_motivo_quarentena":QUAR[i]}); LOG.append((i,"quarentena",QUAR[i])); continue
        if i in (120217,120218,120219,120220): q["statement"]=SONETO+q["statement"]; LOG.append((i,"texto","soneto (texto-base das questões 13 a 16) incluído"))
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
