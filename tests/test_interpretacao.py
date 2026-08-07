"""Testes do julgamento/formatação de cartões (`ui/interpretacao.py`).

Sem Qt — `Resultado`/`Projeto` construídos à mão, sem rodar `core/methods`.
"""
from __future__ import annotations

from dataclasses import replace

from soloref.core.methods.base import Resultado
from soloref.core.models import Projeto
from soloref.ui import interpretacao


def _cartao(cartoes, rotulo):
    for c in cartoes:
        if c.rotulo == rotulo:
            return c
    raise AssertionError(f"cartão {rotulo!r} não encontrado em {cartoes!r}")


# --------------------------------------------------------------------------- #
# Bishop — selo ADEQUADO / INSUFICIENTE
# --------------------------------------------------------------------------- #
def test_bishop_fs_acima_do_alvo_e_adequado():
    projeto = replace(Projeto(), reforco=replace(Projeto().reforco, fs_alvo=1.5))
    resultado = Resultado(metodo="Bishop", fator_seguranca=1.95,
                           extras={"xc_m": 1.0, "yc_m": 2.0, "R_m": 3.0})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Bish", resultado, projeto), "Fator de segurança"
    )
    assert cartao.selo_texto == "ADEQUADO"
    assert cartao.selo_ok is True


def test_bishop_fs_abaixo_do_alvo_e_insuficiente():
    projeto = replace(Projeto(), reforco=replace(Projeto().reforco, fs_alvo=1.5))
    resultado = Resultado(metodo="Bishop", fator_seguranca=1.0,
                           extras={"xc_m": 1.0, "yc_m": 2.0, "R_m": 3.0})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Bish", resultado, projeto), "Fator de segurança"
    )
    assert cartao.selo_texto == "INSUFICIENTE"
    assert cartao.selo_ok is False


def test_bishop_fs_igual_ao_alvo_e_adequado():
    # FS >= alvo (fronteira inclusive), conforme especificado.
    projeto = replace(Projeto(), reforco=replace(Projeto().reforco, fs_alvo=1.5))
    resultado = Resultado(metodo="Bishop", fator_seguranca=1.5, extras={})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Bish", resultado, projeto), "Fator de segurança"
    )
    assert cartao.selo_texto == "ADEQUADO"


# --------------------------------------------------------------------------- #
# Geossintético — OK / ALERTA
# --------------------------------------------------------------------------- #
def test_geossintetico_dimensionamento_fechado_e_ok():
    resultado = Resultado(metodo="Geossintético", extras={
        "n_camadas": 11, "Sv_m": 0.36, "Tadm_kN_m": 16.5, "Tmax_total_kN_m": 66.7,
    })
    cartao = _cartao(
        interpretacao.cartoes_resultado("Ref", resultado, Projeto()), "Nº de camadas"
    )
    assert cartao.selo_texto == "OK"
    assert cartao.selo_ok is True


def test_geossintetico_sv_invalido_e_alerta():
    resultado = Resultado(metodo="Geossintético", extras={
        "n_camadas": 11, "Sv_m": 0.0, "Tadm_kN_m": 0.0, "Tmax_total_kN_m": 0.0,
    })
    cartao = _cartao(
        interpretacao.cartoes_resultado("Ref", resultado, Projeto()), "Nº de camadas"
    )
    assert cartao.selo_texto == "ALERTA"
    assert cartao.selo_ok is False


def test_geossintetico_sem_camadas_e_alerta():
    resultado = Resultado(metodo="Geossintético", extras={})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Ref", resultado, Projeto()), "Nº de camadas"
    )
    assert cartao.selo_texto == "ALERTA"


# --------------------------------------------------------------------------- #
# Métodos de empuxo — ponto de aplicação e comparação com Rankine
# --------------------------------------------------------------------------- #
def test_ponto_de_aplicacao_h_sobre_3():
    projeto = replace(Projeto(), geometria=replace(Projeto().geometria, altura_H_m=4.0))
    resultado = Resultado(metodo="Rankine", solicitacao_kN_m=53.333,
                           inclinacao_cunha_g=60.0, extras={"Ka": 0.333})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Rank", resultado, projeto), "Ponto de aplicação (H/3)"
    )
    assert cartao.valor == "1.33 m"


def test_rankine_nao_tem_cartao_de_comparacao():
    resultado = Resultado(metodo="Rankine", solicitacao_kN_m=53.333,
                           inclinacao_cunha_g=60.0, extras={})
    cartoes = interpretacao.cartoes_resultado("Rank", resultado, Projeto())
    assert not any(c.rotulo == "Comparação com Rankine" for c in cartoes)


def test_coulomb_11_porcento_abaixo_de_rankine():
    # Mesmo exemplo do enunciado: Coulomb=47.5, Rankine=53.333 -> ~11% abaixo.
    coulomb = Resultado(metodo="Coulomb", solicitacao_kN_m=47.5,
                         inclinacao_cunha_g=54.3, extras={"Ka": 0.297})
    rankine = Resultado(metodo="Rankine", solicitacao_kN_m=53.333,
                         inclinacao_cunha_g=60.0, extras={"Ka": 0.333})
    cartao = _cartao(
        interpretacao.cartoes_resultado("Coul", coulomb, Projeto(), referencia=rankine),
        "Comparação com Rankine",
    )
    assert cartao.valor == "Coulomb 11% abaixo de Rankine"


def test_dois_blocos_acima_de_rankine():
    db = Resultado(metodo="Dois Blocos", solicitacao_kN_m=60.0,
                    inclinacao_cunha_g=30.0, extras={"cunha2_g": 60.0})
    rankine = Resultado(metodo="Rankine", solicitacao_kN_m=50.0,
                         inclinacao_cunha_g=60.0, extras={})
    cartao = _cartao(
        interpretacao.cartoes_resultado("DB", db, Projeto(), referencia=rankine),
        "Comparação com Rankine",
    )
    assert cartao.valor == "Dois Blocos 20% acima de Rankine"


def test_sem_referencia_disponivel_nao_gera_cartao_de_comparacao():
    coulomb = Resultado(metodo="Coulomb", solicitacao_kN_m=47.5,
                         inclinacao_cunha_g=54.3, extras={})
    cartoes = interpretacao.cartoes_resultado("Coul", coulomb, Projeto(), referencia=None)
    assert not any(c.rotulo == "Comparação com Rankine" for c in cartoes)


# --------------------------------------------------------------------------- #
# Estabilidade externa — três selos ADEQUADO/INSUFICIENTE + excentricidade
# --------------------------------------------------------------------------- #
def _resultado_ext(**extras_override):
    extras = {
        "FS_desl": 5.02, "FS_tomb": 11.51, "FS_cap": 14.96,
        "e_m": 0.217, "Pah_kN_m": 66.67, "Pav_kN_m": 0.0,
    }
    extras.update(extras_override)
    return Resultado(metodo="Estabilidade externa", fator_seguranca=5.02, extras=extras)


def test_estabilidade_externa_tudo_adequado():
    projeto = replace(Projeto(), geometria=replace(Projeto().geometria, largura_aterro_B_m=5.0))
    cartoes = interpretacao.cartoes_resultado("Ext", _resultado_ext(), projeto)

    for rotulo in ("Deslizamento (FS)", "Tombamento (FS)", "Capacidade de carga (FS)"):
        cartao = _cartao(cartoes, rotulo)
        assert cartao.selo_texto == "ADEQUADO"
        assert cartao.selo_ok is True

    exc = _cartao(cartoes, "Excentricidade")
    assert exc.selo_texto == "OK"
    assert exc.selo_ok is True


def test_estabilidade_externa_fs_baixo_e_insuficiente():
    # FS_desl=1.0 < alvo 1,5 -> INSUFICIENTE; os outros dois continuam OK.
    projeto = replace(Projeto(), geometria=replace(Projeto().geometria, largura_aterro_B_m=5.0))
    cartoes = interpretacao.cartoes_resultado(
        "Ext", _resultado_ext(FS_desl=1.0), projeto
    )
    desl = _cartao(cartoes, "Deslizamento (FS)")
    assert desl.selo_texto == "INSUFICIENTE"
    assert desl.selo_ok is False
    assert _cartao(cartoes, "Tombamento (FS)").selo_ok is True


def test_estabilidade_externa_excentricidade_fora_do_nucleo_e_alerta():
    projeto = replace(Projeto(), geometria=replace(Projeto().geometria, largura_aterro_B_m=1.0))
    # B/6 = 0,167 m; e=1,086 m está bem fora.
    cartoes = interpretacao.cartoes_resultado(
        "Ext", _resultado_ext(e_m=1.086), projeto
    )
    exc = _cartao(cartoes, "Excentricidade")
    assert exc.selo_texto == "ALERTA"
    assert exc.selo_ok is False


def test_estabilidade_externa_selos_usam_os_alvos_do_metodo_core():
    # Os alvos não são reimplementados em interpretacao.py — vêm direto de
    # MetodoEstabilidadeExterna, fonte única de verdade (Tarefa 1).
    from soloref.core.methods.estabilidade_externa import MetodoEstabilidadeExterna

    projeto = Projeto()
    fs_no_limite = MetodoEstabilidadeExterna.FS_ALVO_TOMBAMENTO
    cartoes = interpretacao.cartoes_resultado(
        "Ext", _resultado_ext(FS_tomb=fs_no_limite), projeto
    )
    assert _cartao(cartoes, "Tombamento (FS)").selo_texto == "ADEQUADO"
