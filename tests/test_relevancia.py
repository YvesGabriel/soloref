"""Testes do mapa de relevância aba/campo por método (`ui/relevancia.py`).

Sem Qt — só confere os dados que `PainelDados` usa para destacar/atenuar
abas e marcar as reservadas.
"""
from __future__ import annotations

from soloref.ui import relevancia


def test_rankine_usa_geometria_aterro_sobrecarga():
    abas = set(relevancia.abas_relevantes("Rank"))
    assert abas == {
        relevancia.ABA_GEOMETRIA, relevancia.ABA_ATERRO, relevancia.ABA_SOBRECARGA,
    }


def test_coulomb_inclui_atrito_blocos_delta():
    campos = relevancia.campos_relevantes("Coul", relevancia.ABA_ATERRO)
    assert "δ" in campos


def test_rankine_nao_inclui_atrito_blocos_delta():
    campos = relevancia.campos_relevantes("Rank", relevancia.ABA_ATERRO)
    assert "δ" not in campos


def test_dois_blocos_igual_coulomb():
    assert (relevancia.abas_relevantes("DB")
            == relevancia.abas_relevantes("Coul"))
    assert (relevancia.campos_relevantes("DB", relevancia.ABA_ATERRO)
            == relevancia.campos_relevantes("Coul", relevancia.ABA_ATERRO))


def test_bishop_nao_usa_sobrecarga():
    assert relevancia.ABA_SOBRECARGA not in relevancia.abas_relevantes("Bish")


def test_geossintetico_usa_reforco():
    assert relevancia.ABA_REFORCO in relevancia.abas_relevantes("Ref")


def test_abas_reservadas_nunca_sao_relevantes_para_nenhum_metodo():
    for sigla in ("Rank", "Coul", "DB", "Bish", "Ref"):
        relevantes = set(relevancia.abas_relevantes(sigla))
        assert not relevantes & set(relevancia.ABAS_RESERVADAS)


def test_sigla_desconhecida_nao_da_erro():
    assert relevancia.abas_relevantes("???") == ()
    assert relevancia.campos_relevantes("???", relevancia.ABA_GEOMETRIA) == ()
