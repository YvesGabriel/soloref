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
    for sigla in ("Rank", "Coul", "DB", "Bish", "Ref", "Ext"):
        relevantes = set(relevancia.abas_relevantes(sigla))
        assert not relevantes & set(relevancia.ABAS_RESERVADAS)


def test_sigla_desconhecida_nao_da_erro():
    assert relevancia.abas_relevantes("???") == ()
    assert relevancia.campos_relevantes("???", relevancia.ABA_GEOMETRIA) == ()


def test_estabilidade_externa_usa_encosta_e_fundacao():
    # A Estabilidade Externa é o que tira "Solo encosta" e "Solo fundação"
    # de ABAS_RESERVADAS — o solo retido (empuxo motor) e o solo de
    # fundação (atrito de base + capacidade de carga) passam a ser
    # consumidos de verdade.
    abas = set(relevancia.abas_relevantes("Ext"))
    assert abas == {
        relevancia.ABA_GEOMETRIA, relevancia.ABA_ATERRO,
        relevancia.ABA_ENCOSTA, relevancia.ABA_FUNDACAO,
        relevancia.ABA_SOBRECARGA,
    }


def test_apenas_face_continua_reservada():
    assert relevancia.ABAS_RESERVADAS == (relevancia.ABA_FACE,)
