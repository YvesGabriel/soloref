"""Testes do Método de Bishop simplificado.

Sem fórmula fechada para o círculo crítico em geral, então os oráculos são
casos-limite auto-verificáveis (talude infinito, φ=0 analítico) e
convergência — ver PLANO_IMPLEMENTACAO.md §3.4.

TODO: falta o benchmark de exemplo resolvido de livro (Das ou Craig)
pedido no plano. Não foi adicionado ainda porque a referência exata
(edição, número do exemplo, valores de entrada/saída) não estava
disponível nesta sessão — pedir ao orientando antes de fechar esta etapa,
e então adicionar aqui um `test_benchmark_livro_*` com os dados
transcritos literalmente (sem arredondar/estimar).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from soloref.core.methods import MetodoBishop
from soloref.core.methods.bishop import _busca_circulo_critico, _fatias, _fs_para_circulo
from tests.casos_literatura import CASOS, monta_projeto

CASO_BISH01 = next(c for c in CASOS if c.id == "BISH-01")


def test_bish01_talude_infinito():
    """φ=30°, β=20°, c=0 -> FS deve tender a tan(φ)/tan(β) = 1,5863."""
    projeto = monta_projeto(CASO_BISH01.entradas)
    resultado = MetodoBishop().calcular(projeto)

    fs_esperado = CASO_BISH01.esperado["fator_seguranca"]
    erro_pct = abs(resultado.fator_seguranca - fs_esperado) / fs_esperado * 100.0
    assert erro_pct <= CASO_BISH01.tolerancia, (
        f"FS={resultado.fator_seguranca} esperado={fs_esperado} erro={erro_pct:.4f}%"
    )


def test_phi_zero_conferido_analiticamente():
    """Para φ=0, Bishop reduz ao caso clássico não-drenado:
    FS = c·L_arco / Σ(W·sinα) — verificado aqui para um círculo específico
    (não o crítico, só uma tentativa qualquer), com L_arco = Σ(bᵢ/cosαᵢ).
    """
    beta = math.radians(20.0)
    H = 4.0
    gamma = 18.0
    c = 25.0
    xc, yc = -3.0, 12.0
    R = math.hypot(xc, yc)
    n_fatias = 300

    fatias = _fatias(xc, yc, R, beta, H, gamma, q=0.0, n_fatias=n_fatias)
    assert fatias is not None
    W, alpha, largura = fatias

    fs_bishop = _fs_para_circulo(xc, yc, beta, H, gamma, phi=0.0, c=c, n_fatias=n_fatias)

    l_arco = largura / np.cos(alpha)
    fs_analitico = c * np.sum(l_arco) / np.sum(W * np.sin(alpha))

    assert fs_bishop == pytest.approx(fs_analitico, rel=1e-9)


def test_convergencia_iteracao_fs():
    """A iteração de ponto fixo do FS converge (mesmo valor com tolerâncias
    diferentes, e o resultado satisfaz a própria equação de ponto fixo).
    """
    beta = math.radians(20.0)
    H, gamma, phi, c = 4.0, 20.0, math.radians(30.0), 5.0
    xc, yc = -4.0, 15.0

    fs_frouxo = _fs_para_circulo(xc, yc, beta, H, gamma, phi, c, tol=1e-3)
    fs_apertado = _fs_para_circulo(xc, yc, beta, H, gamma, phi, c, tol=1e-8)

    assert fs_frouxo == pytest.approx(fs_apertado, abs=1e-2)


def test_convergencia_busca_circulo_critico():
    """A busca do círculo crítico deve achar (aproximadamente) o mesmo FS e
    o mesmo centro com grades de resolução diferente.
    """
    kwargs = dict(beta=math.radians(20.0), H=4.0, gamma=20.0, phi=math.radians(30.0), c=0.0)

    fs_g, xc_g, yc_g, _ = _busca_circulo_critico(n_grade=8, **kwargs)
    fs_f, xc_f, yc_f, _ = _busca_circulo_critico(n_grade=16, **kwargs)

    assert fs_f == pytest.approx(fs_g, rel=1e-3)
    assert xc_f == pytest.approx(xc_g, rel=0.1)
    assert yc_f == pytest.approx(yc_g, rel=0.1)


def test_sanidade():
    projeto = monta_projeto(CASO_BISH01.entradas)
    resultado = MetodoBishop().calcular(projeto)
    assert resultado.fator_seguranca > 0
    assert resultado.extras["R_m"] > 0
    assert resultado.extras["n_fatias"] > 0
