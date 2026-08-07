"""Estabilidade externa (muro de solo reforçado como bloco rígido).

Fonte: PROMPTS_ESTABILIDADE_EXTERNA.md (Parte A) — FHWA GEC-011 e Das
(capacidade de carga, fatores de Vésic); Wesley (2009), *Fundamentals of
Soil Mechanics*, cap. de muros de solo reforçado (benchmark EXT-REF-01).

Trata o maciço reforçado (largura B, altura H) como um bloco rígido e
verifica três modos de falha — deslizamento na base, tombamento em torno
do pé e capacidade de carga da fundação — além do FS global (o mínimo dos
três). Reaproveita `MetodoRankine` para o empuxo motor do solo retido (aba
Solo de encosta), não duplica a fórmula de Ka.

Convenção do empuxo motor: atua inclinado de δ_ret (atrito solo-muro do
solo retido, `solo_encosta.angulo_atrito_blocos_g`, 0 se não informado),
gerando uma componente vertical Pav que ALIVIA a estrutura (soma à normal
na base e ao momento estabilizante) — δ_ret=0 é o caso conservador
(empuxo puramente horizontal); para muros de solo reforçado a convenção
usual (FHWA/Wesley) é δ_ret=φ_ret.

Fonte de φ_base (atrito na base, usado só no deslizamento): por padrão o
solo de FUNDAÇÃO (`fonte_phi_base="fundacao"`); pode ser trocado para o
próprio aterro reforçado (`fonte_phi_base="aterro"`) — necessário para
reproduzir o benchmark EXT-REF-01 (Wesley), que usa o φ do maciço
reforçado como plano de deslizamento. A capacidade de carga usa sempre o
solo de fundação (é o material que efetivamente resiste por baixo).
"""
from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from .base import MetodoAnalise, Resultado
from .rankine import MetodoRankine
from ..models import Projeto, Solo


def fatores_vesic(phi_f_rad: float) -> tuple[float, float, float]:
    """Fatores de capacidade de carga de Vésic (Nc, Nq, Nγ), sapata corrida.

    Função pura (sem depender de `Projeto`/`MetodoAnalise`) para poder ser
    testada isoladamente contra a tabela de referência da Parte A
    (φ=25°→20,72/10,66/10,88; φ=30°→30,14/18,40/22,40; φ=35°→46,12/33,30/48,03).
    """
    tan_phi = math.tan(phi_f_rad)
    Nq = math.exp(math.pi * tan_phi) * math.tan(math.pi / 4 + phi_f_rad / 2) ** 2
    Nc = 5.14 if phi_f_rad == 0.0 else (Nq - 1.0) / tan_phi
    Ngama = 2.0 * (Nq + 1.0) * tan_phi
    return Nc, Nq, Ngama


class MetodoEstabilidadeExterna(MetodoAnalise):
    nome = "Estabilidade externa"
    sigla = "Ext"
    hipoteses = (
        "Trata o maciço reforçado como um bloco rígido e verifica três modos "
        "de falha: deslizamento na base, tombamento em torno do pé e "
        "capacidade de carga da fundação (fatores de Vésic).",
        "O empuxo motor vem do solo retido (aba Solo de encosta), calculado "
        "por Rankine; pode atuar inclinado de δ_ret (atrito solo-muro do "
        "retido) — o padrão δ_ret=0 é conservador (empuxo horizontal).",
        "O atrito de base do deslizamento vem, por padrão, do solo de "
        "fundação; pode ser configurado para usar o do aterro reforçado.",
        "A capacidade de carga usa a largura efetiva de Meyerhof "
        "(B' = B − 2e) e os fatores de Vésic do solo de fundação.",
        "FS global = mínimo entre deslizamento, tombamento e capacidade de "
        "carga.",
    )

    # FS-alvo usuais de projeto (documentados aqui; a UI pode reexpor).
    FS_ALVO_DESLIZAMENTO = 1.5
    FS_ALVO_TOMBAMENTO = 2.0
    FS_ALVO_CAPACIDADE = 2.0

    def __init__(self, fonte_phi_base: str = "fundacao") -> None:
        if fonte_phi_base not in ("fundacao", "aterro"):
            raise ValueError(
                f"fonte_phi_base deve ser 'fundacao' ou 'aterro', "
                f"recebeu {fonte_phi_base!r}"
            )
        self.fonte_phi_base = fonte_phi_base

    # ------------------------------------------------------------------ #
    def _empuxo_motor(self, projeto: Projeto) -> tuple[float, float, float, float]:
        """(Pah, Pav, Ea_solo, Ea_sob) do empuxo motor do solo retido.

        Reutiliza `MetodoRankine` sobre um `Projeto` temporário com
        `solo_aterro = solo_encosta` e retroaterro horizontal forçado
        (i=0) — a inclinação do topo do BLOCO reforçado não é a mesma
        coisa que a inclinação do retroaterro RETIDO, que a Parte A supõe
        horizontal (Ka = tan²(45−φ_ret/2)). Ea_solo/Ea_sob são
        recompostos a partir de Ka (não do `Ea` que `MetodoRankine`
        devolve), porque a Parte A não inclui alívio por coesão do
        retido nessas parcelas.
        """
        g = projeto.geometria
        encosta = projeto.solo_encosta
        H = g.altura_H_m
        q = projeto.sobrecarga.uniforme_q_kN_m2

        projeto_retido = replace(
            projeto,
            solo_aterro=encosta,
            geometria=replace(g, inclinacao_topo_i_g=0.0),
        )
        Ka = MetodoRankine().calcular(projeto_retido).extras["Ka"]

        Ea_solo = 0.5 * Ka * encosta.peso_especifico_kN_m3 * H ** 2
        Ea_sob = Ka * q * H
        Pah = Ea_solo + Ea_sob
        delta_ret_g = encosta.angulo_atrito_blocos_g or 0.0
        Pav = Pah * math.tan(math.radians(delta_ret_g))
        return Pah, Pav, Ea_solo, Ea_sob

    def _solo_base(self, projeto: Projeto) -> Solo:
        return (projeto.solo_aterro if self.fonte_phi_base == "aterro"
                else projeto.solo_fundacao)

    def _deslizamento_tombamento(self, projeto: Projeto) -> dict[str, float]:
        """Núcleo compartilhado por `calcular` e `avisos` — nada aqui roda
        otimização (é tudo fórmula fechada), então é barato o bastante
        para `avisos()` chamar sem violar a regra de "avisos são baratos".
        """
        g = projeto.geometria
        H, B = g.altura_H_m, g.largura_aterro_B_m
        aterro = projeto.solo_aterro
        q = projeto.sobrecarga.uniforme_q_kN_m2

        W = aterro.peso_especifico_kN_m3 * B * H
        Q = q * B
        N = W + Q

        Pah, Pav, Ea_solo, Ea_sob = self._empuxo_motor(projeto)
        N_total = N + Pav  # vertical total na base, já com o alívio de Pav

        solo_base = self._solo_base(projeto)
        phi_base = math.radians(solo_base.angulo_atrito_g)
        c_base = solo_base.coesao_kN_m2
        Fr = N_total * math.tan(phi_base) + c_base * B
        FS_desl = Fr / Pah if Pah > 0 else float("inf")

        M_estab = N * (B / 2.0) + Pav * B
        M_tomb = Ea_solo * (H / 3.0) + Ea_sob * (H / 2.0)
        FS_tomb = M_estab / M_tomb if M_tomb > 0 else float("inf")
        a = (M_estab - M_tomb) / N_total if N_total > 0 else 0.0
        e = B / 2.0 - a

        return {
            "W": W, "Q": Q, "N": N, "N_total": N_total,
            "Pah": Pah, "Pav": Pav,
            "FS_desl": FS_desl, "FS_tomb": FS_tomb, "e": e,
        }

    # ------------------------------------------------------------------ #
    def calcular(self, projeto: Projeto) -> Resultado:
        g = projeto.geometria
        B = g.largura_aterro_B_m
        fundacao = projeto.solo_fundacao

        dt = self._deslizamento_tombamento(projeto)
        N_total, e = dt["N_total"], dt["e"]

        # 3. Capacidade de carga (Vésic, largura efetiva de Meyerhof).
        B_efetivo = max(B - 2.0 * abs(e), 1e-6)
        sigma_v = N_total / B_efetivo
        phi_f = math.radians(fundacao.angulo_atrito_g)
        Nc, Nq, Ngama = fatores_vesic(phi_f)
        D = g.embutimento_m
        gamma_f = fundacao.peso_especifico_kN_m3
        c_f = fundacao.coesao_kN_m2
        q_ult = c_f * Nc + gamma_f * D * Nq + 0.5 * gamma_f * B_efetivo * Ngama
        FS_cap = q_ult / sigma_v if sigma_v > 0 else float("inf")

        fs_global = min(dt["FS_desl"], dt["FS_tomb"], FS_cap)

        extras: dict[str, Any] = {
            "FS_desl": dt["FS_desl"],
            "FS_tomb": dt["FS_tomb"],
            "FS_cap": FS_cap,
            "e_m": e,
            "B_efetivo_m": B_efetivo,
            "sigma_v_kPa": sigma_v,
            "q_ult_kPa": q_ult,
            "Pah_kN_m": dt["Pah"],
            "Pav_kN_m": dt["Pav"],
            "N_kN_m": N_total,
            "Nc": Nc,
            "Nq": Nq,
            "Ngama": Ngama,
        }
        return Resultado(metodo=self.nome, fator_seguranca=fs_global, extras=extras)

    def avisos(self, projeto: Projeto) -> list[str]:
        g = projeto.geometria
        H, B = g.altura_H_m, g.largura_aterro_B_m
        avisos: list[str] = []

        if H > 0 and 0 < B < H / 2:
            avisos.append(
                f"Base estreita (B={B:g} m) para a altura do muro "
                f"(H={H:g} m) — espere fatores de segurança baixos de "
                "deslizamento/tombamento."
            )

        if B > 0:
            dt = self._deslizamento_tombamento(projeto)
            limite = B / 6.0
            if abs(dt["e"]) > limite:
                avisos.append(
                    f"Excentricidade e={dt['e']:.2f} m > B/6={limite:.2f} m "
                    "— a resultante sai do núcleo central da base (tração), "
                    "fora da faixa usual de projeto."
                )
        return avisos
