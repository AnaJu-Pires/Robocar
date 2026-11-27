"""Bombeamento do VM (7,2 V) na frenagem com slow decay: modelo medio do motor + carro + capacitor do VM."""
import math
def sim(C_uF, eta_back, eta_fwd=0.6, v0_cmd=0.7, v1_cmd=0.4, rampa_ms=10, freio='slow', m=0.67, r=0.021,
        R=3.8, ke=0.0708, Vset=7.2, I_q=0.005, dt=1e-5, T=0.6):
    # ke: V por rad/s no eixo de saida (900 rpm em vazio a 7,2 V); R: 7,2 V / 1,9 A de travamento
    C = C_uF * 1e-6
    w = v0_cmd * Vset / ke      # em regime (aprox.)
    VM = Vset; cmd = v0_cmd * 1000; alvo = v1_cmd * 1000; t = 0; vmax = VM; Ereg = 0
    while t < T:
        if cmd > alvo: cmd = max(alvo, cmd - rampa_ms * dt * 1000)
        d = cmd / 1000
        Eb = ke * w
        if freio == 'slow':
            I = (d * VM - Eb) / R               # media: drive (VM) / brake (0)
            Ivm = d * I                         # corrente que sai do VM (negativa = volta)
        else:                                   # fast decay: diodos impedem corrente reversa
            I = max(0.0, (d * VM - Eb) / R) if d * VM > Eb else 0.0
            Ivm = d * I
        Tm = ke * I * (eta_fwd if I > 0 else 1 / eta_back)   # torque no eixo da roda
        F = 2 * Tm / r - 0.15 * m * 9.81 * 0.05             # 2 motores; atrito de rolamento ~5%
        v = w * r
        v += F / m * dt; w = max(0.0, v / r)
        Iin = 2 * Ivm + I_q
        if VM < Vset and Iin > 0: VM = Vset   # o XL4016 so fornece
        else: VM -= Iin / C * dt
        if 2 * Ivm < 0: Ereg += -2 * Ivm * VM * dt
        vmax = max(vmax, VM); t += dt
    return vmax, Ereg
for C in (940, 1880, 3000):
    for eb in (0.3, 0.5, 0.7):
        vm, E = sim(C, eb)
        print(f'C {C:5d} uF, rendimento reverso {eb:.1f}: VM pico {vm:5.1f} V (energia devolvida {E*1000:5.0f} mJ)')
print('fast decay (sem regeneracao):', '%.1f V' % sim(940, 0.7, freio='fast')[0])
print('frear de 0,7 ate 0 em 100 ms, C 1880, rend. 0,5:', '%.1f V' % sim(1880, 0.5, v1_cmd=0.0)[0])
