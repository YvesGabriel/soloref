"""Método de Bishop simplificado (cunha circular, fatias).

Fonte: Bishop (1955), forma "simplificada" (despreza forças entre fatias na
direção horizontal). Ver PLANO_IMPLEMENTACAO.md §3.4.

Geometria do talude: como o modelo (`Geometria`) não tem um campo dedicado
a "talude natural", reaproveitamos `inclinacao_face_beta_g` como o ângulo
do talude a partir da horizontal (mesma convenção já usada no caso de
literatura BISH-01 do dataset) — pé do talude na origem (0,0), face reta
subindo até a altura H, e topo/base horizontais além disso. Círculos de
tentativa são restritos a passar pelo **pé do talude** ("toe circles":
simplificação padrão, reduz a busca a 2 parâmetros — centro (xc, yc); o
raio sai de R = |centro − pé|).

Fórmula (por fatia i, largura bᵢ, ângulo da base αᵢ, peso Wᵢ):
    mα(i) = cos(αᵢ) + sin(αᵢ)·tanφ'/FS
    FS = Σ[ (c'·bᵢ + Wᵢ·tanφ') / mα(i) ] / Σ[Wᵢ·sin(αᵢ)]
Aqui `bᵢ` é a LARGURA da fatia (não o comprimento do arco da base) — essa
é a convenção que faz a fórmula reduzir exatamente ao caso φ=0 clássico
(FS = c·L_arco/ΣW·sinα) e ao limite de talude infinito (FS→tanφ/tanβ,
c=0); ambos conferidos em `tests/test_bishop.py`. FS itself entra dos dois
lados (mα depende de FS) — resolvido por iteração de ponto fixo até
convergir (tolerância configurável).

Busca do círculo crítico: grade grosseira em (xc, yc) + refino local com
`scipy.optimize.minimize`, minimizando FS (o crítico é o de MENOR FS).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

from .base import MetodoAnalise, Resultado
from ..models import Projeto


def _perfil_y(x: np.ndarray, beta: float, H: float) -> np.ndarray:
    """Altura do terreno em x: face do talude (0..x_topo) e topo plano depois."""
    x_topo = H / math.tan(beta)
    return np.where(x <= x_topo, x * math.tan(beta), H)


def _entrada_circulo(xc: float, yc: float, R: float, beta: float, H: float):
    """x onde o círculo (que passa pelo pé, em x=0) volta a cruzar o
    terreno — ou `None` se o círculo não intercepta o perfil do talude.
    """
    x_topo = H / math.tan(beta)
    tb = math.tan(beta)
    a = 1 + tb**2
    b = -2 * xc - 2 * tb * yc
    cc = xc**2 + yc**2 - R**2
    disc = b**2 - 4 * a * cc

    candidatos = []
    if disc >= 0:
        raiz = math.sqrt(disc)
        for sinal in (1, -1):
            xr = (-b + sinal * raiz) / (2 * a)
            if 1e-6 < xr <= x_topo + 1e-9:
                candidatos.append(xr)
    if candidatos:
        return max(candidatos)

    disc2 = R**2 - (H - yc) ** 2
    if disc2 >= 0:
        raiz2 = math.sqrt(disc2)
        for sinal in (1, -1):
            xr = xc + sinal * raiz2
            if xr > x_topo + 1e-9:
                candidatos.append(xr)
    return max(candidatos) if candidatos else None


def _fatias(xc: float, yc: float, R: float, beta: float, H: float, gamma: float,
            q: float, n_fatias: int):
    """Monta as `n_fatias` fatias verticais entre o pé e o ponto de
    entrada do círculo. Devolve (W, alpha, largura) ou `None` se a
    geometria não for válida.
    """
    x_top = _entrada_circulo(xc, yc, R, beta, H)
    if x_top is None or x_top < 1e-6:
        return None

    xs = np.linspace(0.0, x_top, n_fatias + 1)
    largura = xs[1] - xs[0]
    mids = (xs[:-1] + xs[1:]) / 2

    dentro = R**2 - (mids - xc) ** 2
    if np.any(dentro < 0):
        return None
    y_base = yc - np.sqrt(dentro)
    y_topo = _perfil_y(mids, beta, H)
    h = np.clip(y_topo - y_base, 0.0, None)

    W = gamma * h * largura  # sobrecarga q somada abaixo, via q*largura
    dydx = (mids - xc) / np.sqrt(np.maximum(dentro, 1e-12))
    alpha = np.arctan(dydx)
    return W, alpha, largura


def _fs_para_circulo(
    xc: float, yc: float, beta: float, H: float, gamma: float, phi: float,
    c: float, q: float = 0.0, n_fatias: int = 30, tol: float = 1e-5, max_iter: int = 100,
):
    """FS de Bishop simplificado para um círculo específico (passa pelo pé,
    raio = |centro − pé|). Devolve `None` se a geometria/iteração não
    forem válidas para esse centro.
    """
    R = math.hypot(xc, yc)
    fatias = _fatias(xc, yc, R, beta, H, gamma, q, n_fatias)
    if fatias is None:
        return None
    W, alpha, largura = fatias
    if q:
        W = W + q * largura

    FS = 1.5  # chute inicial razoável; a iteração converge rápido
    for _ in range(max_iter):
        malpha = np.cos(alpha) + np.sin(alpha) * math.tan(phi) / FS
        if np.any(np.abs(malpha) < 1e-6):
            return None
        num = np.sum((c * largura + W * math.tan(phi)) / malpha)
        den = np.sum(W * np.sin(alpha))
        if den <= 0:
            return None
        FS_novo = num / den
        if abs(FS_novo - FS) < tol:
            return FS_novo
        FS = FS_novo
    return FS  # não convergiu em max_iter — devolve a última estimativa


def _busca_circulo_critico(
    beta: float, H: float, gamma: float, phi: float, c: float, q: float = 0.0,
    n_grade: int = 12, n_fatias: int = 30,
):
    """Grade grosseira em (xc, yc) + refino local: devolve o círculo (por
    onde passa o pé do talude) de menor FS. Lança `ValueError` se nenhum
    círculo válido for encontrado na grade.
    """
    xcs = np.linspace(-2.0 * H, 10.0 * H, n_grade)
    ycs = np.linspace(0.5 * H, 20.0 * H, n_grade)

    melhor = None
    params = None
    for xc in xcs:
        for yc in ycs:
            FS = _fs_para_circulo(xc, yc, beta, H, gamma, phi, c, q, n_fatias)
            if FS is not None and FS > 0 and (melhor is None or FS < melhor):
                melhor, params = FS, (xc, yc)

    if melhor is None:
        raise ValueError(
            "Busca do círculo crítico não encontrou nenhuma superfície válida "
            "para os parâmetros informados."
        )

    def f(x):
        FS = _fs_para_circulo(x[0], x[1], beta, H, gamma, phi, c, q, n_fatias)
        return FS if FS is not None else 1e6

    resultado = minimize(
        f, x0=np.array(params), method="Nelder-Mead",
        options={"xatol": 1e-6, "fatol": 1e-8, "maxiter": 3000},
    )
    if resultado.fun < melhor:
        melhor, params = resultado.fun, tuple(resultado.x)

    xc, yc = params
    return melhor, xc, yc, math.hypot(xc, yc)


class MetodoBishop(MetodoAnalise):
    nome = "Método de Bishop simplificado"
    sigla = "Bish"
    hipoteses = (
        "Considera superfície de ruptura circular dividida em fatias.",
        "Despreza as forças entre fatias na direção horizontal "
        "(simplificação de Bishop).",
        "Faz iteração até convergência do fator de segurança.",
        "Aplicável a taludes com geometria mais complexa que os métodos de "
        "cunha plana.",
    )

    def calcular(self, projeto: Projeto) -> Resultado:
        g = projeto.geometria
        s = projeto.solo_aterro
        sob = projeto.sobrecarga

        H = g.altura_H_m
        gamma = s.peso_especifico_kN_m3
        c = s.coesao_kN_m2
        q = sob.uniforme_q_kN_m2
        phi = math.radians(s.angulo_atrito_g)
        beta = math.radians(g.inclinacao_face_beta_g)

        FS, xc, yc, R = _busca_circulo_critico(beta, H, gamma, phi, c, q)

        return Resultado(
            metodo=self.nome,
            fator_seguranca=FS,
            extras={
                "xc_m": xc,
                "yc_m": yc,
                "R_m": R,
                "n_fatias": 30,
            },
        )
