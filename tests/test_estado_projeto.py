"""Testes do rastreamento de alterações não salvas (`ui/estado_projeto.py`).

Sem Qt.
"""
from __future__ import annotations

from dataclasses import replace

from soloref.core.models import Projeto
from soloref.ui.estado_projeto import projeto_sujo


def test_dois_projetos_default_iguais_nao_sao_sujos():
    # Instâncias diferentes, mesmos valores — igualdade por valor.
    assert projeto_sujo(Projeto(), Projeto()) is False


def test_mesmo_objeto_nao_e_sujo():
    p = Projeto()
    assert projeto_sujo(p, p) is False


def test_campo_de_geometria_editado_fica_sujo():
    referencia = Projeto()
    atual = replace(referencia, geometria=replace(referencia.geometria, altura_H_m=6.0))
    assert projeto_sujo(atual, referencia) is True


def test_campo_de_solo_editado_fica_sujo():
    referencia = Projeto()
    atual = replace(
        referencia,
        solo_aterro=replace(referencia.solo_aterro, angulo_atrito_g=33.0),
    )
    assert projeto_sujo(atual, referencia) is True


def test_campo_de_reforco_editado_fica_sujo():
    referencia = Projeto()
    atual = replace(referencia, reforco=replace(referencia.reforco, tult_kN_m=50.0))
    assert projeto_sujo(atual, referencia) is True


def test_identificacao_editada_fica_sujo():
    referencia = Projeto()
    atual = replace(
        referencia,
        identificacao=replace(referencia.identificacao, identificacao="Projeto X"),
    )
    assert projeto_sujo(atual, referencia) is True


def test_voltar_ao_valor_original_deixa_de_ser_sujo():
    referencia = Projeto()
    atual = replace(referencia, geometria=replace(referencia.geometria, altura_H_m=6.0))
    assert projeto_sujo(atual, referencia) is True
    atual_de_volta = replace(atual, geometria=replace(atual.geometria, altura_H_m=4.0))
    assert projeto_sujo(atual_de_volta, referencia) is False


def test_salvar_atualiza_a_referencia_e_limpa_sujo():
    referencia = Projeto()
    atual = replace(referencia, geometria=replace(referencia.geometria, altura_H_m=6.0))
    assert projeto_sujo(atual, referencia) is True
    # "Salvar": a nova referência passa a ser o próprio `atual`.
    referencia = atual
    assert projeto_sujo(atual, referencia) is False
