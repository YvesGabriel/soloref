"""Método de Coulomb (cunha plana).

Fonte: Das, *Principles of Geotechnical Engineering* — teoria de Coulomb do
empuxo ativo (caso geral com atrito solo-muro δ e talude de topo i).

Convenção geométrica (ver PLANO_IMPLEMENTACAO.md §3.2):
    θ = 90 − β   (ângulo da face do muro em relação à vertical; β é medido
                  da horizontal em `Geometria.inclinacao_face_beta_g`, com
                  90° = parede vertical ⇒ θ = 0)
    δ = solo_aterro.angulo_atrito_blocos_g   (atrito solo-muro)
    i = geometria.inclinacao_topo_i_g        (inclinação do talude de topo)

Sobrecarga uniforme q: adotamos a convenção de somar o termo `Ka·q·H` ao
empuxo (mesma convenção usada em `rankine.py`), em vez de converter q numa
altura equivalente de solo `heq = q/γ`. As duas convenções coincidem no
caso particular em que a sobrecarga cobre toda a extensão do topo do
aterro; optamos por `Ka·q·H` por ser a forma mais direta de compor com o
resultado da busca de cunha abaixo (a sobrecarga entra como peso adicional
`q·(largura horizontal do topo da cunha)`, e o valor no ângulo crítico
reproduz exatamente `Ka·q·H` — verificado em `tests/test_coulomb.py`).

Faixa de validade: cunha de ruptura plana — rigoroso para 70° ≤ β ≤ 90°;
fora dessa faixa deve-se usar cunha circular (Bishop). Considera o topo do
talude estável e o aterro isotrópico/homogêneo (sem coesão).

Busca de cunha (trial wedge / Culmann): além da fórmula fechada de Ka,
`_busca_cunha` varre o ângulo `ψ` do plano de ruptura tentativa (a partir
da horizontal, com origem no pé do muro) e resolve o equilíbrio de forças
da cunha ABC — peso W (+ sobrecarga), reação R no plano de ruptura (a φ da
normal) e o empuxo Ea na face do muro (a δ da normal) — via o triângulo de
forças (duas equações, duas incógnitas |R| e |Ea|). O `ψ` que maximiza Ea
é a cunha crítica; esse Ea deve coincidir com o da fórmula fechada — são
dois caminhos independentes validando um ao outro (checado nos testes).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize_scalar

from .base import MetodoAnalise, Resultado, aviso_cunha_plana
from ..models import Projeto


def _coeficiente_ka(phi: float, delta: float, theta: float, i: float) -> float:
    """Ka geral de Coulomb (ângulos em radianos)."""
    numerador = math.cos(phi - theta) ** 2
    denominador = (
        math.cos(theta) ** 2
        * math.cos(delta + theta)
        * (
            1
            + math.sqrt(
                (math.sin(phi + delta) * math.sin(phi - i))
                / (math.cos(delta + theta) * math.cos(theta - i))
            )
        )
        ** 2
    )
    return numerador / denominador


def _peso_cunha(H: float, psi: float, theta: float, i: float, q: float):
    """Peso (+ sobrecarga) da cunha ABC para um plano de ruptura tentativa.

    A = pé do muro (origem), B = topo do muro, C = onde o plano tentativo
    (a partir de A, ângulo `psi` da horizontal) encontra a superfície do
    talude (a partir de B, ângulo `i` da horizontal). Devolve `None` se a
    geometria for inválida para esse `psi` (plano não intercepta o talude
    à frente do muro).
    """
    Bx, By = -H * math.tan(theta), H
    A = np.array([[math.cos(psi), -math.cos(i)], [math.sin(psi), -math.sin(i)]])
    b = np.array([Bx, By])
    try:
        s, t = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    if s <= 1e-9 or t < -1e-9:
        return None
    Cx, Cy = s * math.cos(psi), s * math.sin(psi)
    area = 0.5 * abs(Bx * Cy - Cx * By)
    sobrecarga = q * abs(Cx - Bx)  # q atua na largura horizontal do topo BC
    return area, sobrecarga


def _empuxo_wedge(
    H: float, gamma: float, psi: float, theta: float, i: float,
    phi: float, delta: float, q: float,
):
    """Ea da cunha tentativa `psi`, via equilíbrio do triângulo de forças."""
    resultado = _peso_cunha(H, psi, theta, i, q)
    if resultado is None:
        return None
    area, sobrecarga = resultado
    W = gamma * area + sobrecarga

    normal_plano = psi - math.pi / 2
    dir_R = normal_plano - phi
    face_ang = math.atan2(H, -H * math.tan(theta))
    normal_muro = face_ang - math.pi / 2
    dir_Ea = normal_muro + delta

    A = np.array([[math.cos(dir_R), math.cos(dir_Ea)], [math.sin(dir_R), math.sin(dir_Ea)]])
    b = np.array([0.0, W])
    try:
        _, Ea = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        return None
    return Ea


def _busca_cunha(
    H: float, gamma: float, theta: float, i: float, phi: float, delta: float, q: float,
) -> tuple[float, float]:
    """Busca de cunha (trial wedge / Culmann): devolve (ângulo crítico em
    graus, Ea crítico) maximizando o empuxo sobre o ângulo do plano de
    ruptura tentativa `psi`.
    """
    limite_inferior = i + 1e-4
    limite_superior = math.radians(89.9)

    def menos_Ea(psi: float) -> float:
        Ea = _empuxo_wedge(H, gamma, psi, theta, i, phi, delta, q)
        return -Ea if Ea is not None else 1e18

    resultado = minimize_scalar(
        menos_Ea, bounds=(limite_inferior, limite_superior), method="bounded"
    )
    if resultado.fun >= 1e18:
        raise ValueError(
            "Busca de cunha não encontrou nenhuma superfície válida para os "
            "parâmetros informados (ex.: H=0)."
        )
    return math.degrees(resultado.x), -resultado.fun


class MetodoCoulomb(MetodoAnalise):
    nome = "Método de Coulomb"
    sigla = "Coul"
    hipoteses = (
        "Método de cálculo por equilíbrio limite; faz o equilíbrio das "
        "solicitações sobre a cunha de ruptura.",
        "Como considera cunha de ruptura plana, este método só vale para "
        "estruturas cuja inclinação do muro esteja entre 70° e 90°, "
        "inclusive; para inclinações menores que 70° deve-se considerar "
        "cunha de ruptura circular.",
        "Considera a superfície do topo estável, mesmo se inclinada.",
        "Considera o material do aterro isotrópico e homogêneo.",
    )

    def calcular(self, projeto: Projeto) -> Resultado:
        g = projeto.geometria
        s = projeto.solo_aterro
        sob = projeto.sobrecarga

        H = g.altura_H_m
        gamma = s.peso_especifico_kN_m3
        q = sob.uniforme_q_kN_m2
        phi = math.radians(s.angulo_atrito_g)
        delta = math.radians(s.angulo_atrito_blocos_g or 0.0)
        theta = math.radians(90.0 - g.inclinacao_face_beta_g)
        i = math.radians(g.inclinacao_topo_i_g)

        Ka = _coeficiente_ka(phi, delta, theta, i)
        Ea = 0.5 * gamma * H**2 * Ka + Ka * q * H

        cunha_g, Ea_busca = _busca_cunha(H, gamma, theta, i, phi, delta, q)

        return Resultado(
            metodo=self.nome,
            solicitacao_kN_m=Ea,
            inclinacao_cunha_g=cunha_g,
            extras={
                "Ka": Ka,
                "Ea_busca_cunha_kN_m": Ea_busca,
                "theta_g": math.degrees(theta),
                "delta_g": math.degrees(delta),
            },
        )

    def avisos(self, projeto: Projeto) -> list[str]:
        return aviso_cunha_plana(projeto.geometria.inclinacao_face_beta_g)
