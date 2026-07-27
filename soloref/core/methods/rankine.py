"""Método de Rankine (cunha plana, estado ativo).

PLACEHOLDER — implementação numérica nas próximas etapas.
"""
from __future__ import annotations

from .base import MetodoAnalise, Resultado
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
        # TODO: implementar empuxo ativo de Rankine
        return Resultado(metodo=self.nome)
