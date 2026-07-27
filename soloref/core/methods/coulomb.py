"""Método de Coulomb (cunha plana).

PLACEHOLDER — a implementação dos cálculos virá nas próximas etapas
do projeto. Aqui apenas retornamos a estrutura de Resultado para que
a UI possa ser construída e testada.
"""
from __future__ import annotations

from .base import MetodoAnalise, Resultado
from ..models import Projeto


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
        # TODO: implementar equilíbrio de cunha plana de Coulomb
        return Resultado(metodo=self.nome)
