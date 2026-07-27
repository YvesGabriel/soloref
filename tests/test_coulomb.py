"""Testes do Método de Coulomb, lendo o dataset de literatura."""
from __future__ import annotations

import math

import pytest

from soloref.core.methods import MetodoCoulomb, MetodoRankine
from tests.casos_literatura import CASOS, monta_projeto

CASOS_COULOMB = [c for c in CASOS if c.metodo == "coulomb"]


def _extrai_campo(resultado, campo: str):
    if hasattr(resultado, campo):
        return getattr(resultado, campo)
    return resultado.extras.get(campo)


@pytest.mark.parametrize("caso", CASOS_COULOMB, ids=[c.id for c in CASOS_COULOMB])
def test_caso_literatura(caso):
    projeto = monta_projeto(caso.entradas)
    resultado = MetodoCoulomb().calcular(projeto)

    for campo, esperado in caso.esperado.items():
        obtido = _extrai_campo(resultado, campo)
        assert obtido is not None, f"{caso.id}: campo {campo!r} ausente no Resultado"
        erro_pct = abs(obtido - esperado) / abs(esperado) * 100.0 if esperado != 0 else abs(obtido - esperado) * 100.0
        assert erro_pct <= caso.tolerancia, (
            f"{caso.id}: campo {campo!r} esperado={esperado} obtido={obtido} "
            f"erro={erro_pct:.4f}% (tolerância={caso.tolerancia}%)"
        )


def test_coul01_degenerado_coincide_com_rankine_tolerancia_apertada():
    """θ=0, δ=0, i=0: Coulomb deve coincidir com Rankine (Ka=1/3) com erro ~1e-6."""
    caso = next(c for c in CASOS_COULOMB if c.id == "COUL-01")
    projeto = monta_projeto(caso.entradas)

    Ka_coulomb = MetodoCoulomb().calcular(projeto).extras["Ka"]
    Ka_rankine = MetodoRankine().calcular(projeto).extras["Ka"]

    assert Ka_coulomb == pytest.approx(1 / 3, rel=1e-6)
    assert Ka_coulomb == pytest.approx(Ka_rankine, rel=1e-6)


@pytest.mark.parametrize("caso", CASOS_COULOMB, ids=[c.id for c in CASOS_COULOMB])
def test_busca_cunha_coincide_com_formula_fechada(caso):
    """A busca de cunha (trial wedge/Culmann) deve reproduzir a fórmula fechada."""
    projeto = monta_projeto(caso.entradas)
    resultado = MetodoCoulomb().calcular(projeto)

    Ea_fechada = resultado.solicitacao_kN_m
    Ea_busca = resultado.extras["Ea_busca_cunha_kN_m"]

    assert Ea_busca == pytest.approx(Ea_fechada, rel=1e-3)


def test_sanidade():
    for caso in CASOS_COULOMB:
        resultado = MetodoCoulomb().calcular(monta_projeto(caso.entradas))
        assert resultado.solicitacao_kN_m > 0, caso.id
        assert 0.0 < resultado.extras["Ka"] < 1.0, caso.id
