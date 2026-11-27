import json,subprocess,os,sys
W=sys.argv[1]
d=json.load(open('/home/user/extracaoquestoes/_banco/catalogo_drive2/drive2_enem.json'))
for e in d:
    if 2015<=int(e['ano'])<=2019:
        dst=os.path.join(W,'pdf',e['caminho'][len('DRIVE NOVO/'):])
        os.makedirs(os.path.dirname(dst),exist_ok=True)
        if os.path.exists(dst) and os.path.getsize(dst)>10000: continue
        subprocess.run(['curl','-sL',f"https://drive.usercontent.google.com/download?id={e['drive_id']}&export=download&confirm=t",'-o',dst])
        md5=subprocess.run(['md5sum',dst],capture_output=True,text=True).stdout.split()[0]
        print(e['id'],os.path.getsize(dst),'md5ok' if md5==e.get('md5') else 'MD5DIF',flush=True)
