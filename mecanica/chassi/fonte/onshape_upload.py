# Cria um documento no Onshape e importa o STEP do chassi (vira Part Studio + Assembly editaveis)
# e guarda os DXF/PDF de corte no mesmo documento. A chave de API e injetada pelo proxy.
import sys, os, json, time, subprocess
BASE = 'https://cad.onshape.com/api/v6'
PASTA = sys.argv[1]
NOME = sys.argv[2] if len(sys.argv) > 2 else 'Robocar Blitz - chassi v1'
def curl(args):
    r = subprocess.run(['curl', '-sS', '-m', '300', '-H', 'Accept: application/json'] + args + ['-w', '\n%{http_code}'],
                       capture_output=True, text=True)
    body, code = r.stdout.rsplit('\n', 1)
    if not code.startswith('2'):
        raise SystemExit(f'HTTP {code}: {body[:400]} {r.stderr[:200]}')
    return json.loads(body) if body.strip() else {}
doc = curl(['-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps({'name': NOME, 'isPublic': False,
           'description': 'Chassi em chapas de MDF/acrilico cortadas a laser (gerado por script; ver README).'}), f'{BASE}/documents'])
did, wid = doc['id'], doc['defaultWorkspace']['id']
print('documento', did)
tr = curl(['-X', 'POST', '-F', f'file=@{os.path.join(PASTA, "chassi_montado.step")}', '-F', 'formatName=STEP',
           '-F', 'translate=true', '-F', 'flattenAssemblies=false', '-F', 'yAxisIsUp=false', '-F', 'storeInDocument=false',
           f'{BASE}/translations/d/{did}/w/{wid}'])
tid = tr['id']
for _ in range(90):
    st = curl([f'{BASE}/translations/{tid}'])
    if st.get('requestState') in ('DONE', 'FAILED'): break
    time.sleep(5)
print('importacao STEP:', st.get('requestState'), st.get('failureReason'))
for arq in sorted(os.listdir(PASTA)):
    if arq.endswith(('.dxf', '_1x1.pdf')):
        curl(['-X', 'POST', '-F', f'file=@{os.path.join(PASTA, arq)}', '-F', 'translate=false', '-F', 'storeInDocument=true',
              f'{BASE}/blobelements/d/{did}/w/{wid}'])
        print('anexado', arq)
print(f'https://cad.onshape.com/documents/{did}/w/{wid}')
