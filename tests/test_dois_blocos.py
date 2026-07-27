"""Testes do Método dos Dois Blocos — sem fórmula fechada, então os
oráculos são limites/monotonicidade/convergência (ver PLANO_IMPLEMENTACAO.md
§3.3), não comparação direta com um valor de literatura.
"""
from __future__ import annotations

import pytest

from soloref.core.methods import MetodoCoulomb, MetodoDoisBlocos, MetodoRankine
from soloref.core.methods.dois_blocos import _busca_bilinear
from soloref.core.models import Geometria, Projeto, Solo, Sobrecarga


def _projeto_simples(*, phi=30.0, delta=0.0, gamma=20.0, H=4.0, c=0.0, i=0.0, q=0.0):
    """Projeto com parede vertical (θ=0) — geometria simples para os oráculos."""
    return Projeto(
        geometria=Geometria(altura_H_m=H, inclinacao_face_beta_g=90.0, inclinacao_topo_i_g=i),
        solo_aterro=Solo(
            peso_especifico_kN_m3=gamma, coesao_kN_m2=c,
            angulo_atrito_g=phi, angulo_atrito_blocos_g=delta,
        ),
        sobrecarga=Sobrecarga(uniforme_q_kN_m2=q),
    )


def test_limite_inferior_rankine():
    """Para geometria simples (δ=0), a solicitação deve ser >= Ea de Rankine.

    A busca bilinear generaliza a cunha reta única (Rankine/Coulomb são um
    caso particular, ψ1=ψ2); com refino suficiente o máximo encontrado não
    deve ficar abaixo do valor de Rankine. Uma pequena folga (0.5%) é
    aceita por ser uma busca numérica, não uma forma fechada.
    """
    projeto = _projeto_simples()
    Ea_rankine = MetodoRankine().calcular(projeto).solicitacao_kN_m
    Ea_db = MetodoDoisBlocos().calcular(projeto).solicitacao_kN_m

    assert Ea_db >= Ea_rankine * 0.995


def test_proximidade_coulomb_parede_vertical():
    """Parede vertical, δ=0: Dois Blocos deve ficar perto de Coulomb (~poucos %)."""
    projeto = _projeto_simples()
    Ea_coulomb = MetodoCoulomb().calcular(projeto).solicitacao_kN_m
    Ea_db = MetodoDoisBlocos().calcular(projeto).solicitacao_kN_m

    erro_pct = abs(Ea_db - Ea_coulomb) / Ea_coulomb * 100.0
    assert erro_pct < 2.0, f"Dois Blocos={Ea_db:.4f} Coulomb={Ea_coulomb:.4f} erro={erro_pct:.2f}%"


def test_monotonicidade_phi_reduz_solicitacao():
    valores = [
        MetodoDoisBlocos().calcular(_projeto_simples(phi=phi)).solicitacao_kN_m
        for phi in (20.0, 25.0, 30.0, 35.0)
    ]
    assert valores == sorted(valores, reverse=True), valores


def test_monotonicidade_gamma_aumenta_solicitacao():
    valores = [
        MetodoDoisBlocos().calcular(_projeto_simples(gamma=gamma)).solicitacao_kN_m
        for gamma in (15.0, 20.0, 25.0)
    ]
    assert valores == sorted(valores), valores


def test_monotonicidade_altura_aumenta_solicitacao():
    valores = [
        MetodoDoisBlocos().calcular(_projeto_simples(H=H)).solicitacao_kN_m
        for H in (3.0, 4.0, 5.0)
    ]
    assert valores == sorted(valores), valores


def test_convergencia_mesmo_critico_com_refino():
    """A busca deve achar (aproximadamente) o mesmo Ea e a mesma geometria
    crítica com grades de resolução diferente — sinal de que convergiu
    para o ótimo real, não para um artefato de grade grosseira.
    """
    kwargs = dict(H=4.0, gamma=20.0, q=0.0, c=0.0, phi=0.5235987755982988,
                  delta=0.2617993877991494, theta=0.0, i=0.0)  # 30° e 15° em rad

    Ea_grosso, xp_g, psi1_g, psi2_g = _busca_bilinear(n_grade=8, **kwargs)
    Ea_fino, xp_f, psi1_f, psi2_f = _busca_bilinear(n_grade=18, **kwargs)

    assert Ea_fino == pytest.approx(Ea_grosso, rel=1e-3)
    assert psi1_f == pytest.approx(psi1_g, abs=1e-2)
    assert psi2_f == pytest.approx(psi2_g, abs=1e-2)


def test_sanidade():
    resultado = MetodoDoisBlocos().calcular(_projeto_simples())
    assert resultado.solicitacao_kN_m > 0
    assert 0.0 < resultado.extras["cunha1_g"] < 90.0
    assert 0.0 < resultado.extras["cunha2_g"] < 90.0


def test_coesao_reduz_solicitacao():
    """Mais coesão -> solo mais estável -> menor solicitação sobre o muro."""
    sem_coesao = MetodoDoisBlocos().calcular(_projeto_simples(H=6.0, gamma=17.5, phi=20.0, c=0.0))
    com_coesao = MetodoDoisBlocos().calcular(_projeto_simples(H=6.0, gamma=17.5, phi=20.0, c=10.0))
    assert com_coesao.solicitacao_kN_m < sem_coesao.solicitacao_kN_m
