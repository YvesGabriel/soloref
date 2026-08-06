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

    def avisos(self, projeto: Projeto) -> list[str]:
        """Avisos de aplicabilidade do método para o `projeto` dado.

        Calculado só a partir dos dados de entrada (sem rodar `calcular`),
        para poder ser consultado a qualquer momento — inclusive antes de um
        cálculo bem-sucedido. Lista vazia por padrão; cada método sobrescreve
        conforme a faixa de validade já descrita em `hipoteses`.
        """
        return []

    # Futuramente: método para desenhar o esquema específico do método
    # (cunha plana, bilinear, circular, etc.) recebendo um QPainter.


def aviso_cunha_plana(inclinacao_face_beta_g: float) -> list[str]:
    """Aviso compartilhado pelos métodos de cunha plana (Coulomb, Rankine,
    Dois Blocos): fora da faixa 70°-90° a hipótese de cunha plana deixa de
    ser rigorosa (ver `hipoteses` de cada método).
    """
    if inclinacao_face_beta_g < 70:
        return [
            "Método de cunha plana: rigoroso apenas para face entre 70° e "
            f"90° (β atual = {inclinacao_face_beta_g:g}°). Para faces mais "
            "abatidas use Bishop (cunha circular)."
        ]
    return []
