"""Análise com reforço por geossintéticos — equilíbrio-limite / tieback
estilo FHWA GEC-011 / AASHTO "Simplified Method" (ver PLANO_IMPLEMENTACAO.md
§3.5 para a justificativa da escolha da metodologia).

Fórmulas (estabilidade interna, camada a camada):
    σv(z) = γ·z + q                       tensão vertical na profundidade z
    σh(z) = Ka·σv(z)                      Kr = Ka (mesmo Ka de Rankine — ver rankine.py)
    Tmax  = σh(z)·Sv                      tração requerida por camada
    Tadm  = Tult / (RFcr·RFid·RFd)        tração admissível de longo prazo
    Le    ≥ Tmax·FS / (2·σv·Ci·tanφ)      comprimento de ancoragem (arrancamento)
    La    = (H − z)·tan(45° − φ/2)        comprimento dentro da zona ativa
    L     = La + Le

Espaçamento e número de camadas: o espaçamento máximo permitido por
camada, `Sv ≤ Tadm/(Ka·σv·FS)`, fica cada vez menor com a profundidade
(σv cresce com z). Simplificação adotada aqui: dimensiona-se um
espaçamento ÚNICO (uniforme), governado pela condição mais crítica — a
base do maciço (z=H, onde σv é máxima) —, e o número de camadas sai de
N = ⌈H / Sv_máx(H)⌉, Sv = H/N. Essa é uma simplificação conservadora e
comum em pré-dimensionamento (mais simples de construir que espaçamento
variável), documentada aqui para não ser confundida com o método completo
FHWA (que permite Sv variável por camada).

Profundidade de cada camada: cada camada i (i=1..N) representa a zona
tributária [  (i-1)·Sv, i·Sv ], e sua profundidade de projeto é o PONTO
MÉDIO dessa zona, z_i=(i−0.5)·Sv — não o topo nem a base. Essa escolha não
é arbitrária: com pontos médios, Σ Tmax_i reproduz EXATAMENTE (não apenas
aproximadamente) o empuxo ativo de Rankine ½·Ka·γ·H² + Ka·q·H, para
qualquer N — é a regra do ponto médio (retângulo do meio) para integração,
que é exata para uma função linear como σv(z). Isso é o que sustenta o
oráculo de consistência ΣTmax≈Ea_Rankine em `tests/test_geossintetico.py`
(ali a igualdade é quase exata, não uma aproximação grosseira).
"""
from __future__ import annotations

import math

from .base import MetodoAnalise, Resultado
from ..models import Projeto


def _ka_rankine(phi: float) -> float:
    return (1 - math.sin(phi)) / (1 + math.sin(phi))


class MetodoGeossintetico(MetodoAnalise):
    nome = "Reforço com geossintéticos"
    sigla = "Ref"
    hipoteses = (
        "Calcula o número de camadas de geossintético necessárias para "
        "atingir o fator de segurança alvo.",
        "Considera tração admissível do geossintético com fatores de "
        "redução para fluência, danos de instalação e degradação.",
        "Pode ser aplicado em conjunto com qualquer método de cunha "
        "(Coulomb, Rankine, Dois Blocos).",
    )

    def calcular(self, projeto: Projeto) -> Resultado:
        g = projeto.geometria
        s = projeto.solo_aterro
        sob = projeto.sobrecarga
        r = projeto.reforco

        H = g.altura_H_m
        gamma = s.peso_especifico_kN_m3
        q = sob.uniforme_q_kN_m2
        phi = math.radians(s.angulo_atrito_g)
        Ka = _ka_rankine(phi)

        Tadm = r.tult_kN_m / (r.rf_fluencia * r.rf_dano_instalacao * r.rf_degradacao)

        sigma_v_base = gamma * H + q
        if sigma_v_base <= 0:
            raise ValueError("σv na base é <= 0 — geometria/sobrecarga inválidas.")
        Sv_max_base = Tadm / (Ka * sigma_v_base * r.fs_alvo)
        if Sv_max_base <= 0:
            raise ValueError(
                "Espaçamento máximo calculado é <= 0 — Tult insuficiente para "
                "H/γ/q informados."
            )

        n_camadas = max(1, math.ceil(H / Sv_max_base))
        Sv = H / n_camadas

        tan_phi = math.tan(phi)
        camadas = []
        Tmax_total = 0.0
        for i in range(1, n_camadas + 1):
            z = (i - 0.5) * Sv
            sigma_v = gamma * z + q
            sigma_h = Ka * sigma_v
            Tmax = sigma_h * Sv
            La = (H - z) * math.tan(math.radians(45.0) - phi / 2.0)
            Le = (
                (Tmax * r.fs_alvo) / (2 * sigma_v * r.ci_interacao * tan_phi)
                if tan_phi > 0 else float("inf")
            )
            L = La + Le
            Tmax_total += Tmax
            camadas.append({
                "z_m": z, "sigma_v_kN_m2": sigma_v, "Tmax_kN_m": Tmax,
                "La_m": La, "Le_m": Le, "L_m": L,
            })

        return Resultado(
            metodo=self.nome,
            extras={
                "Ka": Ka,
                "Tadm_kN_m": Tadm,
                "n_camadas": n_camadas,
                "Sv_m": Sv,
                "Tmax_total_kN_m": Tmax_total,
                "camadas": camadas,
            },
        )
