"""Método dos Dois Blocos (cunha bilinear).

PLACEHOLDER — implementação nas próximas etapas.
"""
from __future__ import annotations

from .base import MetodoAnalise, Resultado
from ..models import Projeto


class MetodoDoisBlocos(MetodoAnalise):
    nome = "Método dos Dois Blocos"
    sigla = "DB"
    hipoteses = (
        "Método de cálculo por equilíbrio limite; faz o equilíbrio das "
        "solicitações sobre a cunha de ruptura.",
        "Como considera cunha de ruptura bilinear (tenta simular uma cunha "
        "circular), este método vale para estruturas com parede mais "
        "abatida.",
        "Considera a superfície do topo estável, mesmo se inclinada.",
        "Considera o material do aterro isotrópico e homogêneo.",
    )

    def calcular(self, projeto: Projeto) -> Resultado:
        # TODO: implementar equilíbrio de cunha bilinear (dois blocos)
        return Resultado(metodo=self.nome)
