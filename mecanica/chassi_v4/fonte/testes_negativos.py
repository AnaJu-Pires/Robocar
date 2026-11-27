"""Prova que cada verificacao pega o erro: estraga um valor de proposito e confere que ela FALHA.

  python3 testes_negativos.py            # todos (alguns minutos)
  python3 testes_negativos.py material   # so os que tem 'material' no nome
Sai com erro se alguma verificacao deixar passar o defeito plantado (ou se o projeto sem defeito nao passar).
Grava a tabela em ../testes_negativos.md.
"""
import os, sys, time
import shapely.geometry as sg
import modelo, verificacoes as V, pecas
from geometria import Chapa, ret, circ, rasgo, Furo

class FakeModelo:
    def __init__(s, chapas):
        s.chapas = chapas; s.P = dict(modelo.PADRAO)

def com_medida(nome, valor):
    """Troca uma medida de pecas.M durante o teste."""
    def antes():
        com_medida.salvo = pecas.M[nome]['v']; pecas.M[nome]['v'] = valor
    def depois():
        pecas.M[nome]['v'] = com_medida.salvo
    return antes, depois

def falhas(resultados, contendo=''):
    return [r for r in resultados if not r.ok and contendo.lower() in (r.nome + ' ' + r.detalhe).lower()]

def caso(nome, verif, P=None, medida=None, mutar=None, contendo='', modelo_fake=None):
    return dict(nome=nome, verif=verif, P=P or {}, medida=medida, mutar=mutar, contendo=contendo, fake=modelo_fake)

def chapa_com_ilha():
    base = ret(0, 0, 60, 40)
    anel = sg.Point(30, 20).buffer(12).difference(sg.Point(30, 20).buffer(9))   # corte em anel: o miolo cai
    return FakeModelo([Chapa('teste_ilha', base, [Furo(anel, 'anel')])])

def chapa_gravacao_no_furo():
    return FakeModelo([Chapa('teste_gravacao', ret(0, 0, 60, 30), [circ(30, 15, 8, 'furo')], textos=[('TEXTO', 30, 15, 3)])])

def chapa_aba_fina():
    base = ret(0, 0, 60, 30)
    return FakeModelo([Chapa('teste_aba_fina', base, [], abas=[ret(20, 30, 21.5, 40)])])

def _tirar_passa_fio(m):
    """Apaga o passa-fio do P4 no andar 2: o cabo continua passando ali."""
    ch = next(c for c in m.chapas if c.nome == 'andar2')
    ch.furos = [f for f in ch.furos if f.nome != 'passa_fio_p4']
    ch._cache = None

CASOS = [
    caso('regulamento: comprimento > 250 mm (esfera 100 mm mais para a frente)', 'regulamento', P=dict(ESFERA_X=194.0), contendo='comprimento'),
    caso('regulamento: largura > 150 mm (bitola de 140 mm)', 'regulamento', P=dict(BITOLA=140.0), contendo='largura'),
    caso('regulamento: pneu de 120 mm', 'regulamento', medida=('roda', (120.0, 19.0)), contendo='diametro'),
    caso('regulamento: esfera de 18 mm (carro torto)', 'regulamento', medida=('esfera_altura', 18.0), contendo='esfera'),
    caso('interferencia: XL4016 da esquerda 12 mm para fora (bate na parede)', 'interferencia', P=dict(XL_Y=(12.0, -2.0)),
         contendo='xl4016_1'),
    caso('interferencia: Jetson sem espacador (solda encosta no andar 2)', 'interferencia', P=dict(JET_ESPACADOR=0.5),
         contendo='jetson'),
    caso('interferencia: bateria 20 mm para a frente (sai pela direita passando pela roda)', 'interferencia', P=dict(BAT_X0=-26.0),
         contendo='roda'),
    caso('acesso: XL4016 10 mm para tras (trimpots embaixo da Jetson)', 'interferencia', P=dict(XL_X0=20.0), contendo='trimpot'),
    caso('acesso: Jetson 20 mm para tras (em cima do fusivel)', 'interferencia', P=dict(J0=-20.0), contendo='fusivel'),
    caso('acesso: vao de 3 mm em cima do dissipador (sem ar)', 'interferencia', P=dict(AR_DISSIPADOR=3.0), contendo='ar_dissipador'),
    caso('camera: pivo 30 mm mais baixo (camera bate no andar 3 em algum angulo)', 'camera', P=dict(PIVO=(86.0, 116.0)),
         contendo='graus:'),
    caso('camera: angulo nominal de 65 graus (a imagem pega o carro)', 'camera', P=dict(CAM_ANG_NOMINAL=65.0),
         contendo='nao ve o proprio carro'),
    caso('material: furo da esfera a 0,5 mm da borda', 'material', P=dict(ESFERA_MARGEM=0.5), contendo='borda'),
    caso('material: furo da esfera passa da borda (vira entalhe)', 'material', P=dict(ESFERA_MARGEM=-1.0), contendo='ENTALHE'),
    caso('material: pilar em cima da porca do andar 2 (furos se juntam)', 'material', P=dict(PILARES=((-14.0, 6.0), (60.0, 80.0))),
         contendo='juntam'),
    caso('material: chave passando da borda da parede (vira entalhe)', 'material', P=dict(CHAVE_Y=55.0), contendo='ENTALHE'),
    caso('material: corte em anel (o miolo cai: peca que se solta)', 'material', modelo_fake=chapa_com_ilha, contendo='pedacos'),
    caso('material: aba de 1,5 mm (parte fina)', 'material', modelo_fake=chapa_aba_fina, contendo='fina'),
    caso('material: gravacao em cima de furo', 'material', modelo_fake=chapa_gravacao_no_furo, contendo='gravacao'),
    caso('cg: 120 g no alto (tomba antes do limite de curva)', 'cg', P=dict(LASTRO=(120.0, 20.0, 0.0, 140.0)), contendo='tomba'),
    caso('cg: sem limite de curva por software (tomba antes de escorregar)', 'cg', P=dict(A_LAT_MAX=None), contendo='tomba'),
    caso('cg: 80 g de lastro de lado (CG fora do centro)', 'cg', P=dict(LASTRO=(80.0, 0.0, 55.0, 30.0)), contendo='centrado'),
    caso('cg: 150 g de lastro atras (empina)', 'cg', P=dict(LASTRO=(150.0, -60.0, 0.0, 30.0)), contendo='empina'),
    caso('cabos: cabo do motor de 90 mm (curto)', 'cabos', medida=('motor_cabo', 90.0), contendo='precisa'),
    caso('cabos: bitola de 86 mm (fios passam a menos de 3 mm da roda)', 'cabos', P=dict(BITOLA=86.0), contendo='roda'),
    caso('cabos: passa-fio do P4 apagado (fio atravessa o andar 2)', 'cabos', mutar=_tirar_passa_fio, contendo='atravessa'),
    caso('cabos: passa-fio apagado da lista de apoios', 'cabos', mutar=lambda m: m.apoios.pop('pf_p4'), contendo='nao existe'),
    caso('cabos: passa-fio do motor embaixo da placa da ESP32 (cabo atravessa a placa)', 'cabos',
         P=dict(PF3_MOTOR=(20.0, 45.0)), contendo='atravessa a placa'),
    caso('folga: andar 2 com 1 mm de vao em cima dos XL4016 (um XL4016 2 mm mais alto nao cabe)', 'folga',
         P=dict(AR_ANDAR2=1.0), contendo='xl4016'),
    caso('folga: XL4016 a 0,3 mm da parede (cabe, mas sem folga nenhuma)', 'folga', P=dict(XL_Y=(7.0, -2.0)), contendo='parede'),
    caso('cabos: cabo USB de 50 mm', 'cabos', medida=('usb_cabo', 50.0), contendo='precisa'),
    caso('medidas: --para-cortar com medidas estimadas', 'medidas', contendo='conferir'),
    caso('dxf: DXF gravado com a Jetson 1 mm diferente da medida', 'dxf', contendo='Jetson'),
    caso('dxf: furos das pecas compradas cortados em vez de gravados (equipe fura a mao)', 'dxf_cortados', contendo='furar a mao'),
]

def _dxf_desatualizado():
    """Grava o DXF com as medidas atuais e depois 'mede' a Jetson 1 mm maior: o DXF nao confere mais."""
    import tempfile, gerar
    m = modelo.construir()
    folhas = gerar.arranjar(gerar.expandir(m.chapas), m.P['MESA'])
    arq = os.path.join(tempfile.mkdtemp(), 'chapa.dxf')
    arqs = []
    for k, f in enumerate(folhas):
        arqs.append(arq.replace('.dxf', f'_{k}.dxf')); gerar.escrever_dxf(f, arqs[-1])
    antes, depois = com_medida('jet_furos_borda', (89.0, 60.0))
    antes()
    try:
        return gerar.auditar_dxf(arqs, m)
    finally:
        depois()

def _dxf_furos_cortados():
    """Grava o DXF como se os furos das pecas compradas fossem cortados (sem a marca para furar a mao)."""
    import tempfile, gerar
    m = modelo.construir()
    folhas = gerar.arranjar(gerar.expandir(m.chapas), m.P['MESA'])
    arq = os.path.join(tempfile.mkdtemp(), 'chapa.dxf')
    arqs = []
    gerar.FURAR_A_MAO[0] = False
    try:
        for k, f in enumerate(folhas):
            arqs.append(arq.replace('.dxf', f'_{k}.dxf')); gerar.escrever_dxf(f, arqs[-1])
    finally:
        gerar.FURAR_A_MAO[0] = True
    return gerar.auditar_dxf(arqs, m)

def rodar(c):
    antes = depois = None
    if c['medida']:
        antes, depois = com_medida(*c['medida'])
        antes()
    try:
        if c['fake']:
            m = c['fake']()
        else:
            m = modelo.construir(c['P'])
            if c['mutar']:
                c['mutar'](m)
        f = {'regulamento': V.regulamento, 'interferencia': V.interferencia, 'camera': V.camera, 'material': V.material,
             'cg': V.cg, 'folga': V.folga, 'cabos': lambda m_: V.cabos(m_)[0] if not c['mutar'] else _cabos_mutado(m_, c['mutar']),
             'medidas': lambda m_: V.medidas(para_cortar=True), 'dxf': lambda m_: _dxf_desatualizado(),
             'dxf_cortados': lambda m_: _dxf_furos_cortados()}[c['verif']]
        return f(m)
    finally:
        if depois:
            depois()

def _cabos_mutado(m, mutar):
    # verificacoes.cabos reconstroi o modelo; aplicamos a mutacao no modelo que ele usa
    orig = modelo.construir
    def construir_mutado(P=None, verif=False):
        mm = orig(P, verif); mutar(mm); return mm
    V.modelo.construir = construir_mutado
    try:
        return V.cabos(m)[0]
    finally:
        V.modelo.construir = orig

def principal():
    filtro = sys.argv[1] if len(sys.argv) > 1 else ''
    linhas = ['# Testes negativos das verificacoes (gerado por `fonte/testes_negativos.py`)', '',
              'Cada linha planta um defeito de proposito e confere que a verificacao FALHA (pega o defeito).', '',
              '| defeito plantado | verificacao | pegou? | o que ela disse |', '|---|---|---|---|']
    ok_geral = True
    t0 = time.time()
    if not filtro:
        m = modelo.construir()
        R, _ = V.tudo(m)
        base_ok = not any(not r.ok for r in R if r.grupo != 'medidas')
        linhas.append(f"| (nenhum: projeto como esta) | todas | {'passou, como deve' if base_ok else '**FALHOU**'} | "
                      f"{len(R)} verificacoes |")
        print('base:', 'ok' if base_ok else 'FALHOU')
        ok_geral &= base_ok
    for c in CASOS:
        if filtro and filtro not in c['nome']:
            continue
        R = rodar(c)
        achou = falhas(R, c['contendo'])
        pegou = bool(achou)
        ok_geral &= pegou
        det = (achou[0].nome + ': ' + achou[0].detalhe)[:150] if achou else 'NAO PEGOU'
        print(('PEGOU    ' if pegou else 'NAO PEGOU'), c['nome'], '->', det)
        linhas.append(f"| {c['nome']} | {c['verif']} | {'sim' if pegou else '**NAO**'} | {det.replace('|', '/')} |")
    linhas.append('')
    linhas.append(f'Tempo: {time.time() - t0:.0f} s.')
    if not filtro:
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'testes_negativos.md'), 'w').write('\n'.join(linhas) + '\n')
    print('TODOS OS DEFEITOS FORAM PEGOS' if ok_geral else 'ALGUM DEFEITO PASSOU (ou o projeto base falhou)')
    return 0 if ok_geral else 1

if __name__ == '__main__':
    sys.exit(principal())
