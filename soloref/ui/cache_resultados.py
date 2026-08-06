"""Cache de resultados por método — sem Qt.

Dois Blocos e Bishop rodam otimização (`scipy.optimize`) e podem demorar;
trocar de aba não pode parecer travamento. Este cache guarda o último
`Resultado` calculado por método (índice em `_METODOS_POR_ABA`, de
`main_window.py`), válido enquanto o `Projeto` usado naquele cálculo não
mudar — comparado por VALOR via `dataclasses.asdict` (não identidade:
`PainelDados.resultado()` sempre devolve uma instância nova de `Projeto`,
mesmo quando nada mudou). `MainWindow` também chama `invalidar()` a cada
edição (`dadosAlterados`): mais barato do que deixar cada entrada
descobrir sozinha, na próxima consulta, que ficou desatualizada — e
qualquer campo, em princípio, pode afetar qualquer método.
"""
from __future__ import annotations

from dataclasses import asdict

from ..core.methods.base import Resultado
from ..core.models import Projeto


class CacheResultados:
    """Um slot de cache por índice de método.

    `obter(metodo_idx, projeto)` devolve o `Resultado` guardado se foi
    calculado para o MESMO `projeto` (por valor) — "hit". Caso contrário
    (nada guardado ainda para esse método, ou guardado para um projeto
    diferente) devolve `None` — "miss": quem chamou deve recalcular e
    gravar o resultado novo com `guardar`.
    """

    def __init__(self) -> None:
        self._entradas: dict[int, tuple[dict, Resultado]] = {}

    def obter(self, metodo_idx: int, projeto: Projeto) -> Resultado | None:
        entrada = self._entradas.get(metodo_idx)
        if entrada is None:
            return None
        projeto_guardado, resultado = entrada
        if projeto_guardado != asdict(projeto):
            return None
        return resultado

    def guardar(self, metodo_idx: int, projeto: Projeto, resultado: Resultado) -> None:
        self._entradas[metodo_idx] = (asdict(projeto), resultado)

    def invalidar(self) -> None:
        """Limpa o cache inteiro — chamado sempre que os dados do projeto
        mudam (qualquer campo pode, em princípio, afetar qualquer método).
        """
        self._entradas.clear()
