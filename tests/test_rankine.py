"""Testes do Método de Rankine, lendo o dataset de literatura."""
from __future__ import annotations

import pytest

from soloref.core.methods import MetodoRankine
from tests.casos_literatura import CASOS, monta_projeto

CASOS_RANKINE = [c for c in CASOS if c.metodo == "rankine"]


def _extrai_campo(resultado, campo: str):
    if hasattr(resultado, campo):
        return getattr(resultado, campo)
    return resultado.extras.get(campo)


@pytest.mark.parametrize("caso", CASOS_RANKINE, ids=[c.id for c in CASOS_RANKINE])
def test_caso_literatura(caso):
    projeto = monta_projeto(caso.entradas)
    resultado = MetodoRankine().calcular(projeto)

    for campo, esperado in caso.esperado.items():
        obtido = _extrai_campo(resultado, campo)
        assert obtido is not None, f"{caso.id}: campo {campo!r} ausente no Resultado"
        erro_pct = abs(obtido - esperado) / abs(esperado) * 100.0 if esperado != 0 else abs(obtido - esperado) * 100.0
        assert erro_pct <= caso.tolerancia, (
            f"{caso.id}: campo {campo!r} esperado={esperado} obtido={obtido} "
            f"erro={erro_pct:.4f}% (tolerância={caso.tolerancia}%)"
        )


def test_sanidade_rank01():
    resultado = MetodoRankine().calcular(monta_projeto(CASOS[0].entradas))
    assert resultado.solicitacao_kN_m > 0
    assert 0.0 < resultado.extras["Ka"] < 1.0


def test_sanidade_rank02_com_coesao():
    caso = next(c for c in CASOS_RANKINE if c.id == "RANK-02")
    resultado = MetodoRankine().calcular(monta_projeto(caso.entradas))
    assert resultado.solicitacao_kN_m > 0
    assert 0.0 < resultado.extras["Ka"] < 1.0


def test_sanidade_rank03_talude():
    caso = next(c for c in CASOS_RANKINE if c.id == "RANK-03")
    resultado = MetodoRankine().calcular(monta_projeto(caso.entradas))
    assert resultado.solicitacao_kN_m > 0
    assert 0.0 < resultado.extras["Ka"] < 1.0
