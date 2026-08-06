"""Testes da divisão segura por tangente (`ui/geometria_segura.py`).

Sem Qt — é por isso que a lógica foi extraída do widget de desenho: dá pra
testar o caso que motivou a correção (β=0° travando o esquema ilustrativo)
sem abrir nenhuma janela.
"""
from __future__ import annotations

import math

from soloref.ui.geometria_segura import cotg_segura


def test_angulo_reto_nao_satura_e_valor_e_quase_zero():
    # tan(90°) é um float enorme (não exatamente infinito) — a divisão dá
    # um valor praticamente nulo, sem precisar saturar.
    valor, saturou = cotg_segura(4.0, math.radians(90.0))
    assert saturou is False
    assert abs(valor) < 1e-10


def test_angulo_45_graus_devolve_o_proprio_numerador():
    valor, saturou = cotg_segura(4.0, math.radians(45.0))
    assert saturou is False
    assert math.isclose(valor, 4.0, rel_tol=1e-9)


def test_angulo_zero_satura_em_vez_de_dividir_por_zero():
    # Este é o caso real que travava o esquema: tan(0°) == 0.0 exatamente.
    valor, saturou = cotg_segura(4.0, math.radians(0.0))
    assert saturou is True
    assert math.isfinite(valor)
    assert valor > 0


def test_angulo_zero_nao_lanca_excecao():
    # Sanidade extra: nenhuma combinação de numerador/ângulo pode propagar
    # ZeroDivisionError ou qualquer outra exceção.
    for numerador in (-10.0, -1.0, 0.0, 0.5, 4.0, 100.0):
        for angulo_g in (-180, -90, -45, 0, 45, 90, 180):
            valor, _ = cotg_segura(numerador, math.radians(angulo_g))
            assert math.isfinite(valor)


def test_angulo_muito_pequeno_tambem_satura():
    # Não precisa ser exatamente 0° para a divisão virar um valor absurdo
    # de desenhar; ângulos bem pequenos também devem saturar.
    valor, saturou = cotg_segura(4.0, math.radians(0.0001))
    assert saturou is True
    assert math.isfinite(valor)


def test_numerador_zero_nao_quebra():
    valor, saturou = cotg_segura(0.0, math.radians(0.0))
    assert math.isfinite(valor)


def test_valor_saturado_respeita_o_sinal_do_numerador():
    valor_pos, saturou_pos = cotg_segura(5.0, math.radians(0.0))
    valor_neg, saturou_neg = cotg_segura(-5.0, math.radians(0.0))
    assert saturou_pos is True and saturou_neg is True
    assert valor_pos > 0
    assert valor_neg < 0
    assert math.isfinite(valor_pos) and math.isfinite(valor_neg)
