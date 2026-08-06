"""Divisão segura por tangente, para o desenho de geometria — sem Qt.

`EsquemaWidget` usa β/βe (inclinação da face/encosta) como denominador de
`H/tan(β)` para achar a posição horizontal do topo do muro. Esses campos
aceitam 0° na entrada de dados (parede/encosta "deitada", fisicamente
degenerada, mas o usuário pode digitar livremente) — e `tan(0°) == 0.0`
exatamente, o que faz a divisão estourar `ZeroDivisionError` e derrubar o
desenho (e, com ele, o app inteiro: uma exceção dentro de `paintEvent`
corrompe o `QPainter` em uso). `cotg_segura` satura em vez de dividir por
zero, sem impedir o usuário de digitar o que quiser no campo — quem chama
decide o que fazer com o aviso de saturação (ex.: um banner no desenho).
"""
from __future__ import annotations

import math


def cotg_segura(numerador: float, angulo_rad: float,
                 limite_mult: float = 30.0) -> tuple[float, bool]:
    """`numerador / tan(angulo_rad)`, protegido contra ângulos em que
    tan(ângulo) ~ 0 (0°, 180°, ...).

    Em vez de deixar a divisão estourar (ou devolver um float absurdamente
    grande que faria o desenho parecer quebrado), satura no maior valor
    ainda razoável de desenhar — `abs(numerador)` vezes `limite_mult` — e
    devolve `(valor, saturou)`. `saturou=True` sinaliza ao chamador que
    aquele ângulo é degenerado para fins de desenho; o valor digitado pelo
    usuário no campo de entrada não é alterado, só o desenho vira uma
    aproximação.
    """
    limite = max(abs(numerador), 1.0) * limite_mult
    t = math.tan(angulo_rad)
    if abs(t) < 1.0 / limite:
        # Sinal do quociente que a divisão teria, no limite (numerador/t
        # com t→0): positivo quando numerador e t têm o mesmo sinal.
        mesmo_sinal = (numerador >= 0) == (t >= 0)
        return (limite if mesmo_sinal else -limite), True
    valor = numerador / t
    if abs(valor) > limite:
        return math.copysign(limite, valor), True
    return valor, False
