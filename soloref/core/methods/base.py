"""Classe base para todos os métodos de análise.

Deixa a extensão para Bishop / geossintéticos trivial: é só herdar e
implementar `calcular`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..models import Projeto


@dataclass
class Resultado:
    """Resultado genérico de uma análise.

    Deixamos um dicionário livre (`extras`) para que cada método possa
    devolver os campos específicos dele sem poluir a interface comum.
    """
    metodo: str
    solicitacao_kN_m: float = 0.0
    inclinacao_cunha_g: float = 0.0
    fator_seguranca: float = 0.0
    extras: dict[str, Any] = field(default_factory=dict)


class MetodoAnalise(ABC):
    """Contrato mínimo que todo método deve cumprir."""

    nome: str = "Método genérico"
    sigla: str = "???"
    hipoteses: tuple[str, ...] = ()

    @abstractmethod
    def calcular(self, projeto: Projeto) -> Resultado:
        """Roda o método para o projeto dado."""

    # Futuramente: método para desenhar o esquema específico do método
    # (cunha plana, bilinear, circular, etc.) recebendo um QPainter.
