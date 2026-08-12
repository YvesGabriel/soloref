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


def test_bishop_usa_sobrecarga():
    # bishop.py soma q ao peso das fatias no topo do talude — FS muda com q
    # (ex.: exemplo complementar do manual, H=5/β=30/γ=19/φ=25/c=10, cai de
    # 1,95 com q=0 para 1,04 com q=100 kN/m²). A aba precisa ficar destacada
    # quando Bishop está ativo, senão parece que q é ignorado.
    assert relevancia.ABA_SOBRECARGA in relevancia.abas_relevantes("Bish")
    assert "q" in relevancia.campos_relevantes("Bish", relevancia.ABA_SOBRECARGA)


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


def test_nenhuma_aba_reservada():
    # "Face" e "Identificação" foram removidas do modelo (não eram lidas
    # por nenhum método); "Solo encosta"/"Solo fundação" já tinham saído
    # de ABAS_RESERVADAS com a Estabilidade Externa — não sobra nada.
    assert relevancia.ABAS_RESERVADAS == ()
