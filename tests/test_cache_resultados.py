"""Testes do cache de resultados por método (`ui/cache_resultados.py`).

Sem Qt — `Resultado`/`Projeto` construídos à mão, sem rodar `core/methods`.
"""
from __future__ import annotations

from dataclasses import replace

from soloref.core.methods.base import Resultado
from soloref.core.models import Projeto
from soloref.ui.cache_resultados import CacheResultados


def test_miss_quando_cache_vazio():
    cache = CacheResultados()
    assert cache.obter(0, Projeto()) is None


def test_hit_apos_guardar_mesmo_projeto():
    cache = CacheResultados()
    projeto = Projeto()
    resultado = Resultado(metodo="Bishop", fator_seguranca=1.95)
    cache.guardar(3, projeto, resultado)
    assert cache.obter(3, projeto) is resultado


def test_hit_com_instancias_diferentes_mas_iguais():
    # PainelDados.resultado() sempre cria um Projeto novo — o cache tem
    # que comparar por valor, não por identidade do objeto.
    cache = CacheResultados()
    resultado = Resultado(metodo="Dois Blocos", solicitacao_kN_m=63.74)
    cache.guardar(2, Projeto(), resultado)
    assert cache.obter(2, Projeto()) is resultado


def test_miss_quando_projeto_mudou():
    cache = CacheResultados()
    projeto = Projeto()
    resultado = Resultado(metodo="Bishop", fator_seguranca=1.95)
    cache.guardar(3, projeto, resultado)

    projeto_editado = replace(
        projeto, geometria=replace(projeto.geometria, altura_H_m=6.0)
    )
    assert cache.obter(3, projeto_editado) is None


def test_metodos_tem_slots_independentes():
    cache = CacheResultados()
    projeto = Projeto()
    r_coulomb = Resultado(metodo="Coulomb", solicitacao_kN_m=47.5)
    r_bishop = Resultado(metodo="Bishop", fator_seguranca=1.95)
    cache.guardar(0, projeto, r_coulomb)
    cache.guardar(3, projeto, r_bishop)

    assert cache.obter(0, projeto) is r_coulomb
    assert cache.obter(3, projeto) is r_bishop
    assert cache.obter(1, projeto) is None  # nunca guardado


def test_guardar_de_novo_sobrescreve_a_entrada_anterior():
    cache = CacheResultados()
    projeto1 = Projeto()
    projeto2 = replace(projeto1, geometria=replace(projeto1.geometria, altura_H_m=6.0))
    r1 = Resultado(metodo="Bishop", fator_seguranca=1.95)
    r2 = Resultado(metodo="Bishop", fator_seguranca=1.20)

    cache.guardar(3, projeto1, r1)
    cache.guardar(3, projeto2, r2)

    assert cache.obter(3, projeto1) is None  # projeto1 não é mais o guardado
    assert cache.obter(3, projeto2) is r2


def test_invalidar_limpa_todos_os_metodos():
    cache = CacheResultados()
    projeto = Projeto()
    cache.guardar(0, projeto, Resultado(metodo="Coulomb"))
    cache.guardar(3, projeto, Resultado(metodo="Bishop"))

    cache.invalidar()

    assert cache.obter(0, projeto) is None
    assert cache.obter(3, projeto) is None
