# anota o uso de um ajudante: python3 ferramentas_nuvem/classif_uso.py <modelo> <tokens> <lotes separados por virgula>
import json, os, sys, datetime
f = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "unificacao", "classif", "uso.json")
u = json.load(open(f))
u["chamadas"].append({"quando": datetime.datetime.now(datetime.timezone.utc).strftime("%FT%TZ"), "modelo": sys.argv[1],
                      "lotes": sys.argv[3].split(","), "tokens": int(sys.argv[2])})
json.dump(u, open(f, "w"), indent=1)
