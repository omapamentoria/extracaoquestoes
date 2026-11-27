# Catalogo de PDFs: o antigo (_banco/catalogo_debug.json) + o do Drive novo, um arquivo por ano em _banco/catalogo_drive2/
import json,glob,os
R="/home/user/extracaoquestoes"
CAT={d["id"]:d for d in json.load(open(R+"/_banco/catalogo_debug.json"))}
# drive2_*.json (catálogo automático) primeiro; os <ano>.json (feitos à mão pelas sessões) valem por cima
for _f in sorted(glob.glob(R+"/_banco/catalogo_drive2/*.json"),key=lambda f:(os.path.basename(f)[0].isdigit(),f)): CAT.update({d["id"]:d for d in json.load(open(_f))})
