"""Testes da Estabilidade Externa (`core/methods/estabilidade_externa.py`).

Gabarito: PROMPTS_ESTABILIDADE_EXTERNA.md, Parte A — exemplo condutor
(δ_ret=0) e o benchmark de literatura EXT-REF-01 (Wesley, δ_ret=φ_ret=26°).
"""
from __future__ import annotations

import math

import pytest

from soloref.core.methods.estabilidade_externa import (
    MetodoEstabilidadeExterna, fatores_vesic,
)
from tests.casos_literatura import monta_projeto


# --------------------------------------------------------------------------- #
# Fatores de capacidade de carga de Vésic — tabela da Parte A
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("phi_g,Nc_esp,Nq_esp,Ngama_esp", [
    (25.0, 20.72, 10.66, 10.88),
    (30.0, 30.14, 18.40, 22.40),
    (35.0, 46.12, 33.30, 48.03),
])
def test_fatores_vesic(phi_g, Nc_esp, Nq_esp, Ngama_esp):
    Nc, Nq, Ngama = fatores_vesic(math.radians(phi_g))
    assert Nc == pytest.approx(Nc_esp, rel=0.001)
    assert Nq == pytest.approx(Nq_esp, rel=0.001)
    assert Ngama == pytest.approx(Ngama_esp, rel=0.001)


def test_fatores_vesic_phi_zero_usa_nc_classico():
    # Nc=5,14 é o valor clássico (a fórmula geral (Nq-1)/tanφ é 0/0 em φ=0).
    Nc, Nq, Ngama = fatores_vesic(0.0)
    assert Nc == pytest.approx(5.14, rel=0.001)
    assert Nq == pytest.approx(1.0, rel=1e-9)
    assert Ngama == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# Exemplo condutor — bloco H=4, B=5, γ=20, φ=30, c=0, q=10; fundação
# φ=30, c=15, γ=20; solo retido = mesmo φ=30, δ_ret=0 (default).
# --------------------------------------------------------------------------- #
def _projeto_exemplo_condutor():
    return monta_projeto({
        "sobrecarga": {"uniforme_q_kN_m2": 10.0},
    })


def test_exemplo_condutor_forcas_e_empuxo():
    projeto = _projeto_exemplo_condutor()
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    e = resultado.extras

    assert e["N_kN_m"] == pytest.approx(450.0, rel=0.005)
    assert e["Pah_kN_m"] == pytest.approx(66.67, rel=0.005)
    assert e["Pav_kN_m"] == pytest.approx(0.0, abs=1e-9)  # δ_ret=0


def test_exemplo_condutor_fs_deslizamento():
    projeto = _projeto_exemplo_condutor()
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    assert resultado.extras["FS_desl"] == pytest.approx(5.02, rel=0.005)


def test_exemplo_condutor_fs_tombamento():
    projeto = _projeto_exemplo_condutor()
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    assert resultado.extras["FS_tomb"] == pytest.approx(11.51, rel=0.005)
    assert resultado.extras["e_m"] == pytest.approx(0.217, rel=0.01)


def test_exemplo_condutor_fs_capacidade_de_carga():
    projeto = _projeto_exemplo_condutor()
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    e = resultado.extras
    assert e["B_efetivo_m"] == pytest.approx(4.565, rel=0.005)
    assert e["sigma_v_kPa"] == pytest.approx(98.57, rel=0.005)
    assert e["q_ult_kPa"] == pytest.approx(1474.9, rel=0.005)
    assert e["FS_cap"] == pytest.approx(14.96, rel=0.005)


def test_exemplo_condutor_fs_global_e_o_minimo_dos_tres():
    projeto = _projeto_exemplo_condutor()
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    e = resultado.extras
    assert resultado.fator_seguranca == pytest.approx(
        min(e["FS_desl"], e["FS_tomb"], e["FS_cap"])
    )
    # Base larga (B=5) para H=4: tudo estável, sem avisos.
    assert MetodoEstabilidadeExterna().avisos(projeto) == []


# --------------------------------------------------------------------------- #
# EXT-REF-01 — Wesley (2009): H=9, B=3,7; aterro γ=18,2 φ=35; solo retido
# γ=16,8 φ=26 c=0 com δ_ret=φ_ret=26°; φ_base = aterro reforçado (35°);
# sem sobrecarga. Só FS_desl e FS_tomb são citados no benchmark.
# --------------------------------------------------------------------------- #
def _projeto_ext_ref_01():
    return monta_projeto({
        "geometria": {"altura_H_m": 9.0, "largura_aterro_B_m": 3.7},
        "solo_aterro": {
            "peso_especifico_kN_m3": 18.2, "angulo_atrito_g": 35.0,
            "coesao_kN_m2": 0.0,
        },
        "solo_encosta": {
            "peso_especifico_kN_m3": 16.8, "angulo_atrito_g": 26.0,
            "coesao_kN_m2": 0.0, "angulo_atrito_blocos_g": 26.0,
        },
        "sobrecarga": {"uniforme_q_kN_m2": 0.0},
    })


def test_ext_ref_01_empuxo_inclinado():
    projeto = _projeto_ext_ref_01()
    resultado = MetodoEstabilidadeExterna(fonte_phi_base="aterro").calcular(projeto)
    e = resultado.extras
    assert e["Pah_kN_m"] == pytest.approx(265.7, rel=0.01)
    assert e["Pav_kN_m"] == pytest.approx(129.6, rel=0.01)


def test_ext_ref_01_peso_do_bloco():
    projeto = _projeto_ext_ref_01()
    W_esperado = 18.2 * 3.7 * 9.0
    assert W_esperado == pytest.approx(606.1, rel=0.001)
    resultado = MetodoEstabilidadeExterna(fonte_phi_base="aterro").calcular(projeto)
    assert resultado.extras["N_kN_m"] - resultado.extras["Pav_kN_m"] == pytest.approx(
        W_esperado, rel=0.001
    )


def test_ext_ref_01_fs_deslizamento_e_tombamento():
    projeto = _projeto_ext_ref_01()
    resultado = MetodoEstabilidadeExterna(fonte_phi_base="aterro").calcular(projeto)
    assert resultado.extras["FS_desl"] == pytest.approx(1.94, rel=0.01)
    assert resultado.extras["FS_tomb"] == pytest.approx(2.00, rel=0.01)


def test_ext_ref_01_com_phi_base_fundacao_da_resultado_diferente():
    # Sanidade: a fonte de φ_base importa — usar o default (fundação, que
    # no Projeto() é φ=30, mais fraco que os 35° do aterro) muda o FS.
    projeto = _projeto_ext_ref_01()
    fs_aterro = MetodoEstabilidadeExterna(fonte_phi_base="aterro").calcular(projeto)
    fs_fundacao = MetodoEstabilidadeExterna(fonte_phi_base="fundacao").calcular(projeto)
    assert fs_aterro.extras["FS_desl"] != pytest.approx(fs_fundacao.extras["FS_desl"])


def test_fonte_phi_base_invalida_leva_a_value_error():
    with pytest.raises(ValueError):
        MetodoEstabilidadeExterna(fonte_phi_base="invalido")


# --------------------------------------------------------------------------- #
# Sensibilidade: base estreita reprova deslizamento/tombamento.
#
# A Parte A sugere B=2,5 como "caso de sensibilidade" que "deve derrubar"
# os dois FS, mas isso não foi verificado por cálculo lá (ao contrário do
# exemplo condutor e do EXT-REF-01) — e, checando aqui, B=2,5 com H=4 e os
# demais parâmetros do exemplo condutor NÃO reprova (FS_desl≈2,51,
# FS_tomb≈2,88, ambos acima do alvo); nem B=1,5 (FS_desl≈1,51 — a coesão
# c=15 kN/m² do solo de fundação, que entra em Fr=N·tanφ_base+c_base·B,
# ainda segura o suficiente). B=1,0 é o valor que de fato reprova os dois
# com folga, mantendo tudo o mais igual ao exemplo condutor.
# --------------------------------------------------------------------------- #
def test_base_estreita_reprova_deslizamento_e_tombamento():
    projeto = monta_projeto({
        "geometria": {"largura_aterro_B_m": 1.0},
        "sobrecarga": {"uniforme_q_kN_m2": 10.0},
    })
    resultado = MetodoEstabilidadeExterna().calcular(projeto)
    e = resultado.extras

    assert e["FS_desl"] < MetodoEstabilidadeExterna.FS_ALVO_DESLIZAMENTO
    assert e["FS_tomb"] < MetodoEstabilidadeExterna.FS_ALVO_TOMBAMENTO
    assert resultado.fator_seguranca == pytest.approx(
        min(e["FS_desl"], e["FS_tomb"], e["FS_cap"])
    )


def test_base_estreita_gera_aviso_de_excentricidade():
    projeto = monta_projeto({
        "geometria": {"largura_aterro_B_m": 1.0},
        "sobrecarga": {"uniforme_q_kN_m2": 10.0},
    })
    avisos = MetodoEstabilidadeExterna().avisos(projeto)
    assert avisos != []
    assert any("Excentricidade" in a for a in avisos)


def test_fs_baixo_e_menor_que_fs_da_base_larga():
    # Monotonicidade: a mesma geometria com base mais estreita tem que dar
    # FS menor em todos os três modos de falha (mais alívio de peso/atrito
    # perdido do que ganho em qualquer efeito de segunda ordem).
    largo = monta_projeto({"sobrecarga": {"uniforme_q_kN_m2": 10.0}})
    estreito = monta_projeto({
        "geometria": {"largura_aterro_B_m": 1.0},
        "sobrecarga": {"uniforme_q_kN_m2": 10.0},
    })
    r_largo = MetodoEstabilidadeExterna().calcular(largo)
    r_estreito = MetodoEstabilidadeExterna().calcular(estreito)

    assert r_estreito.extras["FS_desl"] < r_largo.extras["FS_desl"]
    assert r_estreito.extras["FS_tomb"] < r_largo.extras["FS_tomb"]
