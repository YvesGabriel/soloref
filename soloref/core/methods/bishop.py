"""Método de Bishop simplificado (cunha circular).

NOVO em relação ao programa original. PLACEHOLDER — implementação
prevista para uma fase posterior do projeto.
"""
from __future__ import annotations

from .base import MetodoAnalise, Resultado
from ..models import Projeto


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
        # TODO: implementar Bishop simplificado com fatias e iteração
        return Resultado(metodo=self.nome)
