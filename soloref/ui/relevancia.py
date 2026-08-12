"""Mapa de relevância: quais abas/campos de entrada cada método consome.

Sem dependência de Qt — só dados, para poder ser testado sem abrir janela.
`PainelDados` (panels.py) usa isso para destacar as abas relevantes e atenuar
as demais quando o usuário troca de método ativo, e para marcar como
"reservadas" as abas cujos campos nenhum método implementado hoje consome.

Fonte de verdade: o que cada `calcular()` de fato lê em `core/methods/*.py`.
"""
from __future__ import annotations

# Chaves das abas de `PainelDados` — mesma ordem em que são montadas.
ABA_GEOMETRIA = "geometria"
ABA_ATERRO = "solo_aterro"
ABA_ENCOSTA = "solo_encosta"
ABA_FUNDACAO = "solo_fundacao"
ABA_SOBRECARGA = "sobrecarga"
ABA_REFORCO = "reforco"

# Abas que hoje não alimentam NENHUM método implementado — reservadas.
# "Solo encosta" e "Solo fundação" saíram daqui quando a Estabilidade
# Externa passou a consumi-las (solo retido / atrito e capacidade de
# carga da fundação, respectivamente); "Face" e "Identificação" foram
# removidas do modelo (não eram lidas por nenhum método), então hoje
# não sobra nenhuma aba reservada.
ABAS_RESERVADAS: tuple[str, ...] = ()

# sigla do método (`MetodoAnalise.sigla`) -> {aba: (campos usados, ...)}.
# Só entram abas efetivamente lidas por `calcular()`; abas em
# `ABAS_RESERVADAS` nunca aparecem aqui.
_RELEVANCIA: dict[str, dict[str, tuple[str, ...]]] = {
    "Rank": {
        ABA_GEOMETRIA: ("H", "β", "i"),
        ABA_ATERRO: ("γ", "φ", "c"),
        ABA_SOBRECARGA: ("q",),
    },
    "Coul": {
        ABA_GEOMETRIA: ("H", "β", "i"),
        ABA_ATERRO: ("γ", "φ", "c", "δ"),
        ABA_SOBRECARGA: ("q",),
    },
    "DB": {
        ABA_GEOMETRIA: ("H", "β", "i"),
        ABA_ATERRO: ("γ", "φ", "c", "δ"),
        ABA_SOBRECARGA: ("q",),
    },
    "Bish": {
        ABA_GEOMETRIA: ("H", "β"),
        ABA_ATERRO: ("γ", "φ", "c"),
        ABA_SOBRECARGA: ("q",),
    },
    "Ref": {
        ABA_GEOMETRIA: ("H",),
        ABA_ATERRO: ("γ", "φ"),
        ABA_SOBRECARGA: ("q",),
        ABA_REFORCO: ("todos",),
    },
    "Ext": {
        ABA_GEOMETRIA: ("H", "B"),
        ABA_ATERRO: ("γ",),
        ABA_ENCOSTA: ("γ", "φ", "δ"),
        ABA_FUNDACAO: ("γ", "φ", "c"),
        ABA_SOBRECARGA: ("q",),
    },
}


def abas_relevantes(sigla: str) -> tuple[str, ...]:
    """Abas de entrada consumidas pelo método de sigla `sigla`.

    Devolve tupla vazia para sigla desconhecida (nenhuma aba destacada).
    """
    return tuple(_RELEVANCIA.get(sigla, {}).keys())


def campos_relevantes(sigla: str, aba: str) -> tuple[str, ...]:
    """Campos daquela aba que o método `sigla` usa (para tooltip/legenda).

    Tupla vazia se a aba não for relevante para o método (ou sigla/aba
    desconhecida).
    """
    return _RELEVANCIA.get(sigla, {}).get(aba, ())
