"""Testes do dimensionamento com geossintéticos.

TODO: falta 1 exemplo resolvido FHWA/livro transcrito literalmente (pedido
no plano). Não incluído porque a referência exata não estava disponível
nesta sessão — mesma pendência anotada em test_bishop.py. Adicionar aqui
um `test_benchmark_fhwa_*` com os números transcritos (sem estimar) assim
que a fonte for confirmada.
"""
from __future__ import annotations

import pytest

from soloref.core.methods import MetodoGeossintetico, MetodoRankine
from tests.casos_literatura import CASOS, monta_projeto

CASO_GEO01 = next(c for c in CASOS if c.id == "GEO-01")


def test_geo01_consistencia_com_rankine():
    """ΣTmax das camadas deve reproduzir o empuxo ativo de Rankine para a
    mesma geometria — quase exatamente, não só "perto": a profundidade de
    projeto de cada camada é o ponto médio da sua zona tributária, e a
    regra do ponto médio integra uma função linear (σv(z)) sem erro,
    qualquer que seja o número de camadas (ver docstring de
    geossintetico.py).
    """
    projeto = monta_projeto(CASO_GEO01.entradas)
    resultado = MetodoGeossintetico().calcular(projeto)
    Ea_rankine = MetodoRankine().calcular(projeto).solicitacao_kN_m

    erro_pct = abs(resultado.extras["Tmax_total_kN_m"] - Ea_rankine) / Ea_rankine * 100.0
    assert erro_pct <= CASO_GEO01.tolerancia, (
        f"Tmax_total={resultado.extras['Tmax_total_kN_m']:.4f} "
        f"Ea_rankine={Ea_rankine:.4f} erro={erro_pct:.4f}%"
    )


def _projeto_base(*, q: float = 0.0, tult_kN_m: float = 40.0):
    from soloref.core.models import Geometria, Projeto, Reforco, Solo, Sobrecarga

    return Projeto(
        geometria=Geometria(altura_H_m=4.0),
        solo_aterro=Solo(peso_especifico_kN_m3=20.0, coesao_kN_m2=0.0, angulo_atrito_g=30.0),
        sobrecarga=Sobrecarga(uniforme_q_kN_m2=q),
        reforco=Reforco(tult_kN_m=tult_kN_m),
    )


def test_monotonicidade_sobrecarga_aumenta_camadas():
    """↑q ⇒ ↑ número de camadas (mais tensão vertical a resistir)."""
    n_camadas = [
        MetodoGeossintetico().calcular(_projeto_base(q=q)).extras["n_camadas"]
        for q in (0.0, 20.0, 60.0)
    ]
    assert n_camadas == sorted(n_camadas), n_camadas
    assert n_camadas[0] < n_camadas[-1]  # tem que mudar de fato, não só empatar


def test_monotonicidade_tult_reduz_camadas():
    """↑Tult ⇒ ↓ número de camadas (cada camada aguenta mais tração)."""
    n_camadas = [
        MetodoGeossintetico().calcular(_projeto_base(tult_kN_m=t)).extras["n_camadas"]
        for t in (20.0, 40.0, 100.0)
    ]
    assert n_camadas == sorted(n_camadas, reverse=True), n_camadas
    assert n_camadas[0] > n_camadas[-1]


def test_sanidade_camadas():
    resultado = MetodoGeossintetico().calcular(_projeto_base())
    assert resultado.extras["n_camadas"] >= 1
    assert resultado.extras["Sv_m"] > 0
    assert len(resultado.extras["camadas"]) == resultado.extras["n_camadas"]
    for camada in resultado.extras["camadas"]:
        assert camada["Tmax_kN_m"] > 0
        assert camada["La_m"] >= 0
        assert camada["Le_m"] > 0
        assert camada["L_m"] == pytest.approx(camada["La_m"] + camada["Le_m"])
