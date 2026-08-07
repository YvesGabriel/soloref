"""Métodos de análise de estabilidade.

Cada método é um arquivo separado e herda de `MetodoAnalise`. Para
adicionar um novo (ex.: Bishop simplificado, ou método com
geossintéticos), basta criar outro módulo e registrá-lo em `MetodoAnalise.todos()`.
"""
from .base import MetodoAnalise, Resultado
from .coulomb import MetodoCoulomb
from .rankine import MetodoRankine
from .dois_blocos import MetodoDoisBlocos
from .bishop import MetodoBishop
from .geossintetico import MetodoGeossintetico
from .estabilidade_externa import MetodoEstabilidadeExterna

__all__ = [
    "MetodoAnalise",
    "Resultado",
    "MetodoCoulomb",
    "MetodoRankine",
    "MetodoDoisBlocos",
    "MetodoBishop",
    "MetodoGeossintetico",
    "MetodoEstabilidadeExterna",
]
