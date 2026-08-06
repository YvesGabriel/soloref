"""Testes do mapeamento Resultado -> Quadro Resumo (`ui/resumo_map.py`).

Sem Qt — `Resultado` construído à mão, sem rodar `core/methods`.
"""
from __future__ import annotations

from soloref.core.methods import (
    MetodoBishop, MetodoCoulomb, MetodoDoisBlocos, MetodoGeossintetico,
    MetodoRankine,
)
from soloref.core.methods.base import Resultado
from soloref.ui.resumo_map import resultado_calculado, resultado_para_resumo


def test_coulomb_preserva_chaves_originais():
    r = Resultado(metodo="Coulomb", solicitacao_kN_m=47.5, inclinacao_cunha_g=54.3,
                   extras={"Ka": 0.297})
    assert resultado_para_resumo(MetodoCoulomb, r) == {
        "coulomb_solicit": 47.5, "coulomb_cunha": 54.3,
    }


def test_rankine_preserva_chaves_originais():
    r = Resultado(metodo="Rankine", solicitacao_kN_m=53.333, inclinacao_cunha_g=60.0,
                   extras={"Ka": 0.333})
    assert resultado_para_resumo(MetodoRankine, r) == {
        "rankine_solicit": 53.333, "rankine_cunha": 60.0,
    }


def test_dois_blocos_preserva_chaves_originais():
    r = Resultado(metodo="Dois Blocos", solicitacao_kN_m=63.74, inclinacao_cunha_g=30.0,
                   extras={"cunha1_g": 30.0, "cunha2_g": 60.0, "inflexao_m": 1.5,
                           "xp_m": 2.6})
    assert resultado_para_resumo(MetodoDoisBlocos, r) == {
        "db_solicit": 63.74, "db_cunha1": 30.0, "db_cunha2": 60.0, "db_inflexao": 1.5,
    }


def test_geossintetico_popula_numero_de_camadas():
    r = Resultado(metodo="Geossintético", extras={
        "n_camadas": 11, "Sv_m": 0.36, "Tadm_kN_m": 16.5, "Tmax_total_kN_m": 66.7,
    })
    assert resultado_para_resumo(MetodoGeossintetico, r) == {"n_camadas": 11}


def test_bishop_popula_fs():
    r = Resultado(metodo="Bishop", fator_seguranca=1.9454,
                   extras={"xc_m": 1.7, "yc_m": 9.4, "R_m": 9.57, "n_fatias": 30})
    assert resultado_para_resumo(MetodoBishop, r) == {"bishop_fs": 1.9454}


def test_bishop_fs_zero_conta_como_nao_calculado():
    # resultado_calculado() usa fator_seguranca != 0 como sinal de que o
    # método rodou; um FS genuinamente 0.0 (não deveria acontecer na
    # prática, mas é o placeholder de "não implementado") não popula linha.
    r = Resultado(metodo="Bishop", fator_seguranca=0.0, extras={})
    assert resultado_para_resumo(MetodoBishop, r) == {}


def test_resultado_placeholder_nao_populado_para_nenhum_metodo():
    placeholder = Resultado(metodo="X")
    assert not resultado_calculado(placeholder)
    for metodo_cls in (MetodoCoulomb, MetodoRankine, MetodoDoisBlocos,
                       MetodoBishop, MetodoGeossintetico):
        assert resultado_para_resumo(metodo_cls, placeholder) == {}
