"""Camada de domínio: modelos de dados e algoritmos de análise.

Importante: nada aqui depende de PySide6/Qt — assim os cálculos podem ser
testados isoladamente e reutilizados em scripts ou outras interfaces.
"""
from .models import (
    Projeto,
    Identificacao,
    Geometria,
    FaceEstrutura,
    Solo,
    Sobrecarga,
)

__all__ = [
    "Projeto",
    "Identificacao",
    "Geometria",
    "FaceEstrutura",
    "Solo",
    "Sobrecarga",
]
