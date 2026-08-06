"""Julgamento e formatação dos cartões do painel de resultados — sem Qt.

Decide O QUE mostrar (cartões, selos de adequação, comparação com Rankine,
ponto de aplicação) a partir de `Resultado`/`Projeto`; a apresentação
visual (cores, ícones, layout) fica inteiramente em `panels.py`. Isolado
da UI para poder ser testado sem abrir janela — mesmo padrão de
`resumo_map.py` e `relevancia.py`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..core.methods.base import Resultado
from ..core.models import Projeto

# Nome curto p/ o texto de comparação ("Coulomb 11% abaixo de Rankine").
_NOME_METODO = {"Coul": "Coulomb", "DB": "Dois Blocos"}


@dataclass(frozen=True)
class Cartao:
    """Um cartão do painel de resultados.

    `selo_texto`/`selo_ok` são opcionais: quando presentes, a UI desenha um
    selo colorido junto do cartão (`selo_ok=True` → verde, `False` →
    vermelho). `selo_ok=None` com `selo_texto` definido não deveria
    acontecer — todo selo emitido por este módulo tem um veredito.
    """
    rotulo: str
    valor: str
    selo_texto: str | None = None
    selo_ok: bool | None = None


def cartoes_resultado(sigla: str, resultado: Resultado, projeto: Projeto,
                       referencia: Resultado | None = None) -> list[Cartao]:
    """Cartões a exibir para o resultado de um método, já com julgamento
    (selos de adequação) e comparações aplicados.

    `referencia` é o `Resultado` de Rankine para o MESMO projeto — usado só
    pelos métodos de empuxo (Coulomb/Dois Blocos) para a comparação
    percentual; ignorado para Rankine/Bishop/Geossintético.
    """
    if sigla == "Ref":
        return _cartoes_geossintetico(resultado)
    if sigla == "Bish":
        return _cartoes_bishop(resultado, projeto)
    return _cartoes_empuxo(sigla, resultado, projeto, referencia)


# --------------------------------------------------------------------------- #
def _cartoes_bishop(resultado: Resultado, projeto: Projeto) -> list[Cartao]:
    e = resultado.extras
    fs = resultado.fator_seguranca
    alvo = projeto.reforco.fs_alvo

    selo_texto = selo_ok = None
    if fs > 0 and alvo > 0:
        selo_ok = fs >= alvo
        selo_texto = "ADEQUADO" if selo_ok else "INSUFICIENTE"

    return [
        Cartao("Fator de segurança", f"{fs:.3f}", selo_texto, selo_ok),
        Cartao("Raio crítico", f"{e.get('R_m', 0.0):.2f} m"),
        Cartao("Centro (x, y)",
               f"({e.get('xc_m', 0.0):.1f}, {e.get('yc_m', 0.0):.1f})"),
    ]


# --------------------------------------------------------------------------- #
def _geossintetico_fechou(resultado: Resultado) -> bool:
    """Nº de camadas finito e positivo, Sv finito e positivo — o mesmo tipo
    de condição que `calcular()` exige (via `ValueError`) para fechar o
    dimensionamento; checado aqui de novo, direto nos `extras`, para o
    cartão refletir o `Resultado` que de fato chegou na UI."""
    e = resultado.extras
    n, sv = e.get("n_camadas"), e.get("Sv_m")
    return (
        n is not None and math.isfinite(n) and n > 0
        and sv is not None and math.isfinite(sv) and sv > 0
    )


def _cartoes_geossintetico(resultado: Resultado) -> list[Cartao]:
    e = resultado.extras
    fechou = _geossintetico_fechou(resultado)
    n, sv = e.get("n_camadas"), e.get("Sv_m")

    n_txt = f"{int(n)}" if n is not None and math.isfinite(n) else "—"
    sv_txt = f"{sv:.3f} m" if sv is not None and math.isfinite(sv) else "—"

    return [
        Cartao("Nº de camadas", n_txt, "OK" if fechou else "ALERTA", fechou),
        Cartao("Espaçamento Sv", sv_txt),
        Cartao("Tadm", f"{e.get('Tadm_kN_m', 0.0):.1f} kN/m"),
        Cartao("ΣTmax", f"{e.get('Tmax_total_kN_m', 0.0):.1f} kN/m"),
    ]


# --------------------------------------------------------------------------- #
def _cartoes_empuxo(sigla: str, resultado: Resultado, projeto: Projeto,
                     referencia: Resultado | None) -> list[Cartao]:
    e = resultado.extras
    cartoes = [Cartao("Empuxo Ea", f"{resultado.solicitacao_kN_m:.1f} kN/m")]
    if "Ka" in e:
        cartoes.append(Cartao("Ka", f"{e['Ka']:.3f}"))
    cartoes.append(Cartao("Inclinação da cunha",
                           f"{resultado.inclinacao_cunha_g:.1f}°"))
    if "cunha2_g" in e:
        cartoes.append(Cartao("2ª cunha", f"{e['cunha2_g']:.1f}°"))

    H = projeto.geometria.altura_H_m
    if H > 0 and resultado.solicitacao_kN_m > 0:
        cartoes.append(Cartao("Ponto de aplicação (H/3)", f"{H / 3:.2f} m"))

    comparacao = _comparacao_rankine(sigla, resultado, referencia)
    if comparacao is not None:
        cartoes.append(Cartao("Comparação com Rankine", comparacao))
    return cartoes


def _comparacao_rankine(sigla: str, resultado: Resultado,
                         referencia: Resultado | None) -> str | None:
    """'Coulomb 11% abaixo de Rankine' — ou `None` se não houver
    referência disponível, se `sigla` já for Rankine, ou se algum dos dois
    empuxos for zero (nada a comparar)."""
    if sigla == "Rank" or referencia is None:
        return None
    if resultado.solicitacao_kN_m <= 0 or referencia.solicitacao_kN_m <= 0:
        return None

    nome = _NOME_METODO.get(sigla, sigla)
    diff_pct = ((resultado.solicitacao_kN_m - referencia.solicitacao_kN_m)
                / referencia.solicitacao_kN_m * 100.0)
    if abs(diff_pct) < 0.5:
        return f"{nome} ≈ Rankine"
    direcao = "abaixo" if diff_pct < 0 else "acima"
    return f"{nome} {abs(diff_pct):.0f}% {direcao} de Rankine"
