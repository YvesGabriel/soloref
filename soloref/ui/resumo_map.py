"""Mapeamento Resultado -> dict do Quadro Resumo (sem dependência de Qt).

Isolado da UI para poder ser testado sem abrir janela nenhuma. Converte o
`Resultado` de um método na estrutura de chaves que `QuadroResumoWidget`
espera, preservando exatamente as chaves usadas na versão MDI original
(coulomb_solicit, rankine_solicit, db_*) e enriquecendo o Dois Blocos com
o ponto de inflexão e a 2ª cunha, além de Bishop (bishop_fs), Geossintético
(n_camadas) e Estabilidade Externa (ext_fs_desl/ext_fs_tomb/ext_fs_cap),
que já vinham em `extras`/`fator_seguranca`.
"""
from __future__ import annotations

from ..core.methods import (
    MetodoCoulomb, MetodoRankine, MetodoDoisBlocos, MetodoBishop,
    MetodoGeossintetico, MetodoEstabilidadeExterna, Resultado,
)


def resultado_calculado(resultado: Resultado) -> bool:
    """Distingue um `Resultado` real de um placeholder vazio.

    Um método não implementado devolve `Resultado(metodo=...)` com
    solicitação/cunha zeradas, FS zerado e `extras` vazio.
    """
    return (
        bool(resultado.extras)
        or resultado.solicitacao_kN_m != 0.0
        or resultado.inclinacao_cunha_g != 0.0
        or resultado.fator_seguranca != 0.0
    )


def resultado_para_resumo(metodo_cls, resultado: Resultado) -> dict:
    """Devolve o dict de chaves do Quadro Resumo para um dado método.

    Métodos sem linha própria no quadro devolvem {} — a coluna ainda é
    criada (com a geometria), mas sem célula de resultado.
    """
    if not resultado_calculado(resultado):
        return {}

    if metodo_cls is MetodoCoulomb:
        return {
            "coulomb_solicit": resultado.solicitacao_kN_m,
            "coulomb_cunha": resultado.inclinacao_cunha_g,
        }
    if metodo_cls is MetodoRankine:
        return {
            "rankine_solicit": resultado.solicitacao_kN_m,
            "rankine_cunha": resultado.inclinacao_cunha_g,
        }
    if metodo_cls is MetodoDoisBlocos:
        e = resultado.extras
        return {
            "db_solicit": resultado.solicitacao_kN_m,
            "db_cunha1": e.get("cunha1_g", resultado.inclinacao_cunha_g),
            "db_cunha2": e.get("cunha2_g"),
            "db_inflexao": e.get("inflexao_m"),
        }
    if metodo_cls is MetodoGeossintetico:
        return {"n_camadas": resultado.extras.get("n_camadas")}
    if metodo_cls is MetodoBishop:
        return {"bishop_fs": resultado.fator_seguranca}
    if metodo_cls is MetodoEstabilidadeExterna:
        e = resultado.extras
        return {
            "ext_fs_desl": e.get("FS_desl"),
            "ext_fs_tomb": e.get("FS_tomb"),
            "ext_fs_cap": e.get("FS_cap"),
        }
    # Métodos futuros sem linha dedicada no quadro caem aqui.
    return {}
