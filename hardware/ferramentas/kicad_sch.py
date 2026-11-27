"""Escreve um esquematico do KiCad (formato do KiCad 7, abre no 7 ao 10) a partir de uma lista de pecas e redes.

Cada pino ligado recebe um rotulo de rede (label) na ponta: o desenho fica em blocos legiveis e a ligacao e exata.
Os simbolos vem das bibliotecas do proprio KiCad (copiados para dentro do arquivo, como o KiCad faz).
Depois de gravar, `conferir()` pede a netlist ao kicad-cli (o KiCad le o arquivo) e compara com as redes pedidas.
"""
import os
import re
import subprocess
import sys
import tempfile
import uuid as _uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'placa_esp32', 'ferramentas'))
from netlist_texto import parse, kids, kid, val, lib_pins, xform  # noqa: E402

LIBS = '/usr/share/kicad/symbols'
for _c in (os.environ.get('KICAD_SYMBOL_DIR', ''), '/usr/share/kicad/symbols', 'C:/Program Files/KiCad/10.0/share/kicad/symbols'):
    if _c and os.path.isdir(_c):
        LIBS = _c
        break


def _u():
    return str(_uuid.uuid4())


def _bloco(texto, inicio):
    """Texto do s-expression que comeca em `inicio` (parenteses balanceados, respeitando strings)."""
    prof, i, em_str = 0, inicio, False
    while True:
        ch = texto[i]
        if em_str:
            if ch == '\\':
                i += 1
            elif ch == '"':
                em_str = False
        elif ch == '"':
            em_str = True
        elif ch == '(':
            prof += 1
        elif ch == ')':
            prof -= 1
            if prof == 0:
                return texto[inicio:i + 1]
        i += 1


def simbolo(lib_id):
    """(texto do simbolo para lib_symbols, pinos) de 'Biblioteca:Nome'."""
    lib, nome = lib_id.split(':')
    txt = open(os.path.join(LIBS, lib + '.kicad_sym'), encoding='utf-8').read()
    m = re.search(r'\n\s*\(symbol "' + re.escape(nome) + r'"', txt)
    if not m:
        raise KeyError(lib_id)
    bloco = _bloco(txt, txt.index('(', m.start()))
    if '(extends ' in bloco[:200]:
        raise ValueError(f'{lib_id} herda de outro simbolo (extends): use um simbolo sem heranca')
    bloco = bloco.replace(f'(symbol "{nome}"', f'(symbol "{lib_id}"', 1)
    return bloco, lib_pins(parse(bloco))


class Esquema:
    def __init__(self, projeto, titulo, data, rev='1'):
        self.projeto, self.titulo, self.data, self.rev = projeto, titulo, data, rev
        self.raiz = _u()
        self.libs = {}
        self.itens = []          # textos ja formatados
        self.pecas = []          # (ref, lib_id, pinos -> rede)

    def peca(self, ref, lib_id, valor, pegada, x, y, rot=0, redes=None, nota=None):
        """Coloca um simbolo com o 'centro' em (x, y) mm (grade de 1,27). redes: {numero do pino: rede}."""
        if lib_id not in self.libs:
            self.libs[lib_id] = simbolo(lib_id)
        _, pinos = self.libs[lib_id]
        redes = redes or {}
        pin_txt = ''.join(f'\n    (pin "{p["num"]}" (uuid {_u()}))' for p in pinos if p['unit'] in (0, 1))
        def prop(nome, v, dx, dy, esconde=False):
            return (f'\n    (property "{nome}" "{v}" (at {x + dx:.2f} {y + dy:.2f} 0)\n      (effects (font (size 1.27 1.27))'
                    f'{" hide" if esconde else ""})\n    )')
        self.itens.append(
            f'  (symbol (lib_id "{lib_id}") (at {x:.2f} {y:.2f} {rot}) (unit 1)\n    (in_bom yes) (on_board yes) (dnp no)'
            f'\n    (uuid {_u()})'
            + prop('Reference', ref, 0, -5.5) + prop('Value', valor, 0, 5.5) + prop('Footprint', pegada, 0, 0, True)
            + prop('Datasheet', '~', 0, 0, True) + pin_txt
            + f'\n    (instances\n      (project "{self.projeto}"\n        (path "/{self.raiz}" (reference "{ref}") (unit 1))\n'
              f'      )\n    )\n  )')
        for p in pinos:
            if p['unit'] not in (0, 1):
                continue
            px, py = xform(p['x'], p['y'], x, y, rot, None)
            rede = redes.get(p['num'])
            if rede:
                self.itens.append(f'  (label "{rede}" (at {px:.2f} {py:.2f} 0) (fields_autoplaced)\n'
                                  f'    (effects (font (size 1.27 1.27)) (justify left bottom))\n    (uuid {_u()})\n  )')
            else:
                self.itens.append(f'  (no_connect (at {px:.2f} {py:.2f}) (uuid {_u()}))')
        self.pecas.append((ref, lib_id, {k: v for k, v in redes.items()}))
        if nota:
            self.texto(nota, x - 6, y + 9, 1.0)

    def texto(self, s, x, y, tam=1.5):
        s = s.replace('"', "'")
        self.itens.append(f'  (text "{s}" (at {x:.2f} {y:.2f} 0)\n    (effects (font (size {tam} {tam})) (justify left bottom))\n'
                          f'    (uuid {_u()})\n  )')

    def gravar(self, arq):
        libs = '\n'.join('    ' + t.replace('\n', '\n  ') for t, _ in self.libs.values())
        txt = (f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {self.raiz})\n\n  (paper "A4")\n\n'
               f'  (title_block\n    (title "{self.titulo}")\n    (date "{self.data}")\n    (rev "{self.rev}")\n'
               f'    (company "Robocar Blitz")\n    (comment 1 "Gerado por script; conferido pelo kicad-cli (netlist)")\n  )\n\n'
               f'  (lib_symbols\n{libs}\n  )\n\n' + '\n\n'.join(self.itens) +
               '\n\n  (sheet_instances\n    (path "/" (page "1"))\n  )\n)\n')
        with open(arq, 'w', encoding='utf-8') as f:
            f.write(txt)


def netlist_kicad(arq_sch):
    """Netlist que o PROPRIO KiCad le do esquematico: {rede: {(ref, pino)}}. Rotulos locais viram '/NOME'."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'x.net')
        r = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, arq_sch],
                           capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError('kicad-cli nao leu o esquematico: ' + r.stdout + r.stderr)
        s = parse(open(out, encoding='utf-8').read())
    redes = {}
    for n in kids(kid(s, 'nets'), 'net'):
        nome = val(n, 'name').lstrip('/')
        nos = {(val(no, 'ref'), val(no, 'pin')) for no in kids(n, 'node')}
        if nome.startswith('unconnected-'):
            continue
        redes[nome] = nos
    return redes


def conferir(arq_sch, esperado):
    """Lista de diferencas entre a netlist do KiCad e as redes esperadas ({rede: {(ref, pino)}})."""
    lida = netlist_kicad(arq_sch)
    erros = []
    for rede, nos in esperado.items():
        if lida.get(rede) != nos:
            erros.append(f'esquematico, rede {rede}: KiCad leu {sorted(lida.get(rede, set()))}, esperado {sorted(nos)}')
    for rede in lida:
        if rede not in esperado:
            erros.append(f'esquematico: rede {rede} a mais: {sorted(lida[rede])}')
    return erros
