"""Camada de domínio: modelos de dados e algoritmos de análise.

Importante: nada aqui depende de PySide6/Qt — assim os cálculos podem ser
testados isoladamente e reutilizados em scripts ou outras interfaces.
"""
from .models import (
    Projeto,
    Geometria,
    Solo,
    Sobrecarga,
    Reforco,
)

__all__ = [
    "Projeto",
    "Geometria",
    "Solo",
    "Sobrecarga",
    "Reforco",
]
