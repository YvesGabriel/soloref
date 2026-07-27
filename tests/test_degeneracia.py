"""Casos degenerados/limite de todos os métodos, num só lugar.

Ver PLANO_IMPLEMENTACAO.md §4.2. Cada teste aqui é um oráculo forte: um
caso especial em que um método deve coincidir exatamente (ou quase) com
outro método mais simples, ou com um limite conhecido — pega a maioria dos
erros de sinal/formulação sem depender de nenhum valor externo de livro.
À medida que novos métodos forem implementados, seus casos degenerados
(Dois Blocos → Coulomb/Rankine para geometria simples; Bishop → talude
infinito; Geossintético → ΣTmax ≈ Ea de Rankine) entram aqui também.
"""
from __future__ import annotations

import pytest

from soloref.core.methods import MetodoCoulomb, MetodoRankine
from tests.casos_literatura import CASOS, monta_projeto


def test_coulomb_degenerado_theta0_delta0_i0_igual_rankine():
    """θ=0 (parede vertical), δ=0 (sem atrito muro-solo), i=0 (topo horizontal):
    o Ka geral de Coulomb deve colapsar exatamente para o de Rankine.
    """
    caso = next(c for c in CASOS if c.id == "COUL-01")
    projeto = monta_projeto(caso.entradas)

    Ka_coulomb = MetodoCoulomb().calcular(projeto).extras["Ka"]
    Ka_rankine = MetodoRankine().calcular(projeto).extras["Ka"]

    assert Ka_coulomb == pytest.approx(Ka_rankine, rel=1e-6)
