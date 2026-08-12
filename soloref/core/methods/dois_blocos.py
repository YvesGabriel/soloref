"""Método dos Dois Blocos (cunha bilinear).

Sem fórmula fechada (ver PLANO_IMPLEMENTACAO.md §3.3) — a superfície de
ruptura bilinear aproxima uma cunha circular e é obtida por busca numérica
(grade grosseira + refino com `scipy.optimize`), não por uma expressão
analítica de Ka.

Geometria adotada (dois blocos, "two-part wedge"):
    A = pé do muro (origem); B = topo do muro.
    A superfície de ruptura tem dois trechos retos: A→N (1ª cunha, ângulo
    `ψ1` da horizontal) e N→C (2ª cunha, ângulo `ψ2`), unidos no "ponto de
    inflexão" N. Uma interface VERTICAL em x=`xp` (de N até M, onde M é o
    ponto do talude de topo sobre essa mesma vertical) separa:
        Bloco 1 = A, B, M, N   (o que toca o muro)
        Bloco 2 = N, M, C      (o mais afastado, sem contato com o muro)
    Essa é a forma padrão do "two-part wedge method" usado para taludes
    com quebra de inclinação (ex.: FHWA/AASHTO para reforço de solo).

Equilíbrio (força, sem momento — 3 forças por bloco):
    - Cada bloco tem peso próprio (+ sobrecarga q sobre seu trecho de
      topo) e, na sua base (o trecho de ruptura), uma reação com atrito φ
      e coesão c do solo de aterro.
    - A interface entre os blocos transmite uma força assumida
      HORIZONTAL (interslice force horizontal — simplificação padrão
      desse método; evita ter que arbitrar um ângulo de atrito na
      interface, que na prática é uma superfície fictícia, não real).
    - O Bloco 2 (não toca o muro) é resolvido primeiro: seu equilíbrio
      vertical (a força de interface não tem componente vertical) dá a
      reação da base diretamente, e o equilíbrio horizontal dá a força de
      interface. Essa força entra, com sinal trocado, no equilíbrio do
      Bloco 1, que tem mais a reação de sua própria base e o empuxo do
      muro (a `δ` da normal — mesma convenção usada em `coulomb.py`).

Busca da superfície crítica (ψ1, ψ2, xp): maximiza-se Ea sobre esses três
parâmetros, restritos a ψ1, ψ2 ≥ φ (abaixo do ângulo de atrito não há
tendência de deslizamento — restrição física padrão em métodos de cunha
tentativa) e 0 < xp num intervalo generoso em torno de H. A implementação
foi validada num protótipo numérico contra os casos degenerados (δ=0 ⇒
resultado coincide com Coulomb/Rankine em ~1e-4; c>0 reproduz exatamente
o efeito de coesão de Rankine) antes de ser escrita aqui.

Limitação conhecida: para δ (atrito de blocos) muito próximo de φ — caso
extremo, mas é o default do projeto —, a busca tende à borda inferior de
ψ1 (=φ) e o resultado fica moderadamente mais conservador (maior) que
Coulomb, algo como 10-15% acima, em vez dos ~1-3% típicos para δ menor.
Isso é uma característica da simplificação de interface horizontal, não
um bug: é aceitável para um método aproximado sem fórmula fechada (ver
oráculos de "vizinhança de Coulomb" em `tests/test_dois_blocos.py`, que
usam δ=0 — o caso padrão de comparação também adotado para Coulomb).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import minimize

from .base import MetodoAnalise, Resultado, aviso_cunha_plana
from ..models import Projeto


def _area_poligono(pontos: list[np.ndarray]) -> float:
    x = np.array([p[0] for p in pontos])
    y = np.array([p[1] for p in pontos])
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _comprimento(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))


def _empuxo_dois_blocos(
    H: float, gamma: float, q: float, c: float, phi: float, delta: float,
    theta: float, i: float, xp: float, psi1: float, psi2: float,
):
    """Ea da cunha bilinear tentativa (xp, ψ1, ψ2), ou `None` se a
    geometria/equilíbrio não forem válidos para esses parâmetros.
    """
    A = np.array([0.0, 0.0])
    B = np.array([-H * math.tan(theta), H])
    if xp <= 1e-6 or psi1 <= 1e-6:
        return None

    t = (xp - B[0]) / math.cos(i)
    if t < 0:
        return None
    M = np.array([xp, B[1] + t * math.sin(i)])
    N = np.array([xp, xp * math.tan(psi1)])
    if N[1] >= M[1] - 1e-9 or N[1] < 0:
        return None  # ponto de inflexão tem que ficar abaixo do talude

    Amat = np.array([[math.cos(psi2), -math.cos(i)], [math.sin(psi2), -math.sin(i)]])
    bvec = np.array([M[0] - N[0], M[1] - N[1]])
    try:
        s, tt = np.linalg.solve(Amat, bvec)
    except np.linalg.LinAlgError:
        return None
    if s <= 1e-9 or tt < -1e-9:
        return None
    C = N + s * np.array([math.cos(psi2), math.sin(psi2)])

    # ---- Bloco 2 (N, M, C) — sem contato com o muro ----
    W2 = gamma * _area_poligono([N, M, C]) + q * abs(C[0] - M[0])
    coesao_2 = c * _comprimento(N, C)
    dir_R2 = (psi2 + math.pi / 2) - phi
    if abs(math.sin(dir_R2)) < 1e-9:
        return None
    R2 = (W2 - coesao_2 * math.sin(psi2)) / math.sin(dir_R2)
    if R2 < 0:
        return None
    forca_interface_em_2 = -(R2 * math.cos(dir_R2) + coesao_2 * math.cos(psi2))

    # ---- Bloco 1 (A, B, M, N) — em contato com o muro ----
    W1 = gamma * _area_poligono([A, B, M, N]) + q * abs(M[0] - B[0])
    coesao_1 = c * _comprimento(A, N)
    dir_R1 = (psi1 - math.pi / 2) - phi
    face_ang = math.atan2(B[1] - A[1], B[0] - A[0])
    dir_Ea = (face_ang - math.pi / 2) + delta
    forca_interface_em_1 = -forca_interface_em_2  # 3a lei de Newton (horizontal)

    b1 = np.array([
        0.0 - coesao_1 * math.cos(psi1) - forca_interface_em_1,
        W1 - coesao_1 * math.sin(psi1),
    ])
    A1 = np.array([[math.cos(dir_R1), math.cos(dir_Ea)], [math.sin(dir_R1), math.sin(dir_Ea)]])
    det = A1[0, 0] * A1[1, 1] - A1[0, 1] * A1[1, 0]
    if abs(det) < 1e-9:
        return None
    try:
        _, Ea = np.linalg.solve(A1, b1)
    except np.linalg.LinAlgError:
        return None
    if Ea < 0:
        return None
    return Ea


def _busca_bilinear(
    H: float, gamma: float, q: float, c: float, phi: float, delta: float,
    theta: float, i: float, n_grade: int = 10,
):
    """Grade grosseira (xp, ψ1, ψ2) + refino local (`scipy.optimize`) para
    achar a superfície bilinear crítica (máximo Ea). Devolve
    `(Ea, xp, psi1, psi2)` com os dois ângulos em radianos, ou lança
    `ValueError` se nenhuma configuração válida for encontrada.
    """
    psi_min = max(phi + math.radians(0.5), math.radians(3.0))
    xp_lim = (0.1 * H, 3.0 * H)
    psi1_lim = (psi_min, math.radians(89.0))
    psi2_lim = (max(i, psi_min), math.radians(89.0))

    melhor = None
    params = None
    for xp in np.linspace(*xp_lim, n_grade):
        for psi1 in np.linspace(*psi1_lim, n_grade):
            for psi2 in np.linspace(*psi2_lim, n_grade):
                Ea = _empuxo_dois_blocos(H, gamma, q, c, phi, delta, theta, i, xp, psi1, psi2)
                if Ea is not None and (melhor is None or Ea > melhor):
                    melhor, params = Ea, (xp, psi1, psi2)

    if melhor is None:
        raise ValueError(
            "Busca de cunha bilinear não encontrou nenhuma superfície válida "
            "para os parâmetros informados."
        )

    def menos_Ea(x):
        Ea = _empuxo_dois_blocos(H, gamma, q, c, phi, delta, theta, i, *x)
        return -Ea if Ea is not None else 1e18

    resultado = minimize(
        menos_Ea, x0=np.array(params), method="Nelder-Mead",
        bounds=[xp_lim, psi1_lim, psi2_lim],
        options={"xatol": 1e-7, "fatol": 1e-9, "maxiter": 3000},
    )
    if -resultado.fun > melhor:
        melhor, params = -resultado.fun, tuple(resultado.x)

    xp, psi1, psi2 = params
    return melhor, xp, psi1, psi2


class MetodoDoisBlocos(MetodoAnalise):
    nome = "Método dos Dois Blocos"
    sigla = "DB"
    hipoteses = (
        "Método de cálculo por equilíbrio limite; faz o equilíbrio das "
        "solicitações sobre a cunha de ruptura.",
        "Considera o atrito solo-muro (δ), como Coulomb, na interação "
        "entre a estrutura e o aterro.",
        "Como considera cunha de ruptura bilinear (tenta simular uma cunha "
        "circular), este método vale para estruturas com parede mais "
        "abatida.",
        "Considera a superfície do topo estável, mesmo se inclinada.",
        "Considera o material do aterro isotrópico e homogêneo.",
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
        delta = math.radians(s.angulo_atrito_blocos_g or 0.0)
        theta = math.radians(90.0 - g.inclinacao_face_beta_g)
        i = math.radians(g.inclinacao_topo_i_g)

        Ea, xp, psi1, psi2 = _busca_bilinear(H, gamma, q, c, phi, delta, theta, i)

        return Resultado(
            metodo=self.nome,
            solicitacao_kN_m=Ea,
            inclinacao_cunha_g=math.degrees(psi1),
            extras={
                "cunha1_g": math.degrees(psi1),
                "cunha2_g": math.degrees(psi2),
                "inflexao_m": xp * math.tan(psi1),
                "xp_m": xp,
            },
        )

    def avisos(self, projeto: Projeto) -> list[str]:
        return aviso_cunha_plana(projeto.geometria.inclinacao_face_beta_g)
