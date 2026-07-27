"""Análise com reforço por geossintéticos.

NOVO em relação ao programa original. PLACEHOLDER — vai compor com os
métodos de cunha plana, calculando o número e espaçamento de camadas
necessárias para garantir o fator de segurança alvo.
"""
from __future__ import annotations

from .base import MetodoAnalise, Resultado
from ..models import Projeto


class MetodoGeossintetico(MetodoAnalise):
    nome = "Reforço com geossintéticos"
    sigla = "Ref"
    hipoteses = (
        "Calcula o número de camadas de geossintético necessárias para "
        "atingir o fator de segurança alvo.",
        "Considera tração admissível do geossintético com fatores de "
        "redução para fluência, danos de instalação e degradação.",
        "Pode ser aplicado em conjunto com qualquer método de cunha "
        "(Coulomb, Rankine, Dois Blocos).",
    )

    def calcular(self, projeto: Projeto) -> Resultado:
        # TODO: implementar dimensionamento de camadas de reforço
        return Resultado(metodo=self.nome)
