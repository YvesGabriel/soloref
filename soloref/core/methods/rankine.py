"""Método de Rankine (cunha plana, estado ativo).

Fonte: Das, *Principles of Geotechnical Engineering* e Craig, *Soil
Mechanics* — capítulos de empuxo de terra, teoria de Rankine.

Faixa de validade: rigoroso apenas para parede vertical e retroaterro
horizontal (caso geral com coesão e sobrecarga). Para retroaterro inclinado
(i ≠ 0) sem coesão, usa-se a forma de Rankine para talude (Ka em função de
i e φ; não há trinca de tração nesse caso, pois pressupõe c=0). Como
considera cunha de ruptura plana, só vale rigorosamente para inclinação do
muro β entre 70° e 90°; fora dessa faixa é usado como aproximação (ver
`hipoteses`).
"""
from __future__ import annotations

import math

from .base import MetodoAnalise, Resultado, aviso_cunha_plana
from ..models import Projeto


class MetodoRankine(MetodoAnalise):
    nome = "Método de Rankine"
    sigla = "Rank"
    hipoteses = (
        "Considera o estado de tensões ativas (proposta de Rankine).",
        "Considera as solicitações atuando na parede da estrutura.",
        "Como considera cunha de ruptura plana, este método só vale para "
        "estruturas cuja inclinação do muro esteja entre 70° e 90°, "
        "inclusive; a inclinação da cunha é definida como sendo o 45° "
        "mais metade do ângulo de atrito do solo de aterro.",
        "Se a parede da estrutura não for vertical, o método não é "
        "rigorosamente aplicável.",
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
        i = g.inclinacao_topo_i_g

        if i != 0.0 and c == 0.0:
            # Retroaterro inclinado, sem coesão — Rankine para talude.
            i_rad = math.radians(i)
            cos_i = math.cos(i_rad)
            cos_phi = math.cos(phi)
            raiz = math.sqrt(cos_i**2 - cos_phi**2)
            Ka = cos_i * (cos_i - raiz) / (cos_i + raiz)
        else:
            # Retroaterro horizontal (caso geral, com coesão/sobrecarga).
            Ka = (1 - math.sin(phi)) / (1 + math.sin(phi))

        Ea = 0.5 * Ka * gamma * H**2 + Ka * q * H - 2 * c * H * math.sqrt(Ka)
        cunha = 45.0 + s.angulo_atrito_g / 2.0
        z0 = max(0.0, (2 * c) / (gamma * math.sqrt(Ka)) - q / gamma) if gamma > 0 else 0.0

        return Resultado(
            metodo=self.nome,
            solicitacao_kN_m=Ea,
            inclinacao_cunha_g=cunha,
            extras={"Ka": Ka, "z0_m": z0},
        )

    def avisos(self, projeto: Projeto) -> list[str]:
        g = projeto.geometria
        s = projeto.solo_aterro
        avisos = aviso_cunha_plana(g.inclinacao_face_beta_g)
        if g.inclinacao_face_beta_g < 90.0 and s.coesao_kN_m2 == 0.0:
            avisos.append(
                "Rankine é rigoroso apenas para parede vertical (β = 90°); "
                f"β atual = {g.inclinacao_face_beta_g:g}°."
            )
        return avisos
