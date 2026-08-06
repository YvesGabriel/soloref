"""Rastreamento de alterações não salvas — sem Qt.

`MainWindow` guarda o último `Projeto` salvo ou carregado como referência
(`_projeto_salvo`) e usa `projeto_sujo` para decidir, a qualquer momento,
se há alterações pendentes — usado para mostrar/esconder o "*" no título
da janela e para perguntar antes de descartar (Novo / Abrir / fechar).
"""
from __future__ import annotations

from ..core.models import Projeto


def projeto_sujo(atual: Projeto, referencia: Projeto) -> bool:
    """`True` se `atual` difere de `referencia` — o último `Projeto`
    salvo ou carregado.

    Dataclasses geram `__eq__` recursivo por valor (`Projeto` e todas as
    suas seções aninhadas), então isso cobre qualquer campo editado em
    qualquer aba, sem precisar listar campo por campo.
    """
    return atual != referencia
