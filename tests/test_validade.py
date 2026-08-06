"""Testes da API de avisos de aplicabilidade (`MetodoAnalise.avisos`).

Não testamos o texto exato dos avisos (frágil, e não é o que importa) — só a
presença/ausência de aviso para cada faixa de validade, conforme já descrito
nas `hipoteses` de cada método.
"""
from __future__ import annotations

from soloref.core.methods import (
    MetodoBishop, MetodoCoulomb, MetodoDoisBlocos, MetodoGeossintetico,
    MetodoRankine,
)
from tests.casos_literatura import monta_projeto


def _projeto_beta(beta_g: float, **extra_solo):
    return monta_projeto({
        "geometria": {"inclinacao_face_beta_g": beta_g},
        "solo_aterro": extra_solo,
    } if extra_solo else {"geometria": {"inclinacao_face_beta_g": beta_g}})


# --------------------------------------------------------------------------- #
# Coulomb / Rankine / Dois Blocos — cunha plana (70°-90°)
# --------------------------------------------------------------------------- #
def test_coulomb_beta_90_sem_aviso_cunha_plana():
    assert MetodoCoulomb().avisos(_projeto_beta(90.0)) == []


def test_coulomb_beta_45_gera_aviso_cunha_plana():
    assert MetodoCoulomb().avisos(_projeto_beta(45.0)) != []


def test_rankine_beta_70_sem_aviso_cunha_plana():
    avisos = MetodoRankine().avisos(_projeto_beta(70.0))
    assert not any("cunha plana" in a.lower() for a in avisos)


def test_rankine_beta_45_gera_aviso_cunha_plana():
    avisos = MetodoRankine().avisos(_projeto_beta(45.0))
    assert any("cunha plana" in a.lower() for a in avisos)


def test_rankine_beta_90_sem_coesao_sem_aviso_parede_vertical():
    # β=90 é exatamente vertical: nenhum aviso de verticalidade.
    avisos = MetodoRankine().avisos(_projeto_beta(90.0, coesao_kN_m2=0.0))
    assert not any("vertical" in a.lower() for a in avisos)


def test_rankine_beta_80_sem_coesao_gera_aviso_parede_vertical():
    avisos = MetodoRankine().avisos(_projeto_beta(80.0, coesao_kN_m2=0.0))
    assert any("vertical" in a.lower() for a in avisos)


def test_dois_blocos_beta_90_sem_aviso_cunha_plana():
    assert MetodoDoisBlocos().avisos(_projeto_beta(90.0)) == []


def test_dois_blocos_beta_45_gera_aviso_cunha_plana():
    assert MetodoDoisBlocos().avisos(_projeto_beta(45.0)) != []


# --------------------------------------------------------------------------- #
# Bishop — cunha circular (faces abatidas, β < 70°)
# --------------------------------------------------------------------------- #
def test_bishop_beta_90_gera_aviso_face_vertical():
    avisos = MetodoBishop().avisos(_projeto_beta(90.0))
    assert avisos != []
    assert any("vertical" in a.lower() for a in avisos)


def test_bishop_beta_30_sem_aviso():
    assert MetodoBishop().avisos(_projeto_beta(30.0)) == []


def test_bishop_beta_75_gera_aviso_face_ingreme_sem_ser_degenerada():
    # Entre 70° e 89°: avisa que a face é íngreme demais para Bishop, mas
    # não que o círculo degenera (isso só a partir de 89°).
    avisos = MetodoBishop().avisos(_projeto_beta(75.0))
    assert any("íngremes" in a or "Coulomb" in a for a in avisos)
    assert not any("degenera" in a.lower() for a in avisos)


# --------------------------------------------------------------------------- #
# Geossintético — Tult insuficiente para o espaçamento mínimo
# --------------------------------------------------------------------------- #
def test_geossintetico_tult_suficiente_sem_aviso():
    projeto = monta_projeto({})  # defaults: Tult=40, H=4, γ=20 — folgado
    assert MetodoGeossintetico().avisos(projeto) == []


def test_geossintetico_tult_insuficiente_gera_aviso():
    # Tadm = tult/(RFcr·RFid·RFd) = 0 ⇒ Sv_max <= 0 (mesma condição de
    # ValueError em `calcular`, aqui só como aviso textual).
    projeto = monta_projeto({"reforco": {"tult_kN_m": 0.0}})
    assert MetodoGeossintetico().avisos(projeto) != []
