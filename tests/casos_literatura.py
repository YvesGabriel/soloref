"""Dataset de casos de validação — fonte única de verdade.

Casos vêm da literatura e das fórmulas/casos-limite fechados verificados no
`PLANO_IMPLEMENTACAO.md` (seção 4.1). Cada `CasoLiteratura` monta um
`Projeto` a partir de `entradas` (dict aninhado que sobrescreve os defaults
de `Projeto`, seção por seção) e o runner de validação compara a saída do
método (`Resultado`) contra `esperado`, dentro de `tolerancia` (erro
relativo, em %).

Convenção assumida para os campos de `esperado` que não existem em
`Resultado` diretamente (`solicitacao_kN_m`, `inclinacao_cunha_g`,
`fator_seguranca`): eles devem aparecer em `Resultado.extras` com a mesma
chave, seguindo o exemplo do cookbook em GUIA_DESENVOLVEDOR.md (`extras={"Ka": Ka}`).
Quando cada método for implementado, usar essas chaves para que os casos
abaixo passem a validar sem precisar reescrever o dataset:

    - Rankine:  extras["Ka"], extras["z0_m"] (profundidade da trinca de tração)
    - Coulomb:  extras["Ka"]
    - Bishop:   fator_seguranca (campo padrão de Resultado)
    - Geossintético: extras["Tmax_total_kN_m"] (soma de Tmax de todas as camadas)

Casos com `fonte` iniciando em "degenerado"/"limite"/"consistência" são
oráculos auto-verificáveis (não vêm de um livro específico); os demais citam
a formulação fechada usada para conferir o valor numérico.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from soloref.core.methods import (
    MetodoBishop,
    MetodoCoulomb,
    MetodoDoisBlocos,
    MetodoEstabilidadeExterna,
    MetodoGeossintetico,
    MetodoRankine,
)
from soloref.core.models import Projeto

# Mapeia o `metodo` de cada caso para a classe que sabe calculá-lo.
METODOS = {
    "rankine": MetodoRankine,
    "coulomb": MetodoCoulomb,
    "dois_blocos": MetodoDoisBlocos,
    "bishop": MetodoBishop,
    "geossintetico": MetodoGeossintetico,
    "externa": MetodoEstabilidadeExterna,
}


@dataclass
class CasoLiteratura:
    id: str
    metodo: str
    fonte: str
    entradas: dict[str, Any] = field(default_factory=dict)
    esperado: dict[str, float] = field(default_factory=dict)
    tolerancia: float = 0.5  # erro relativo aceitável, em %
    # kwargs do construtor do método (ex.: MetodoEstabilidadeExterna
    # aceita fonte_phi_base — necessário pro benchmark EXT-REF-01, que usa
    # o φ do aterro reforçado em vez do padrão "fundacao"). Vazio por
    # padrão: todo método existente continua instanciado sem argumentos.
    metodo_kwargs: dict[str, Any] = field(default_factory=dict)


def monta_projeto(entradas: dict[str, Any]) -> Projeto:
    """Constrói um `Projeto` aplicando `entradas` sobre os defaults.

    `entradas` é um dict cujas chaves são os nomes das seções de `Projeto`
    (`geometria`, `solo_aterro`, `solo_encosta`, `solo_fundacao`,
    `sobrecarga`, `face`, `identificacao`) e cujos valores são dicts de
    overrides para os campos daquela seção. Seções/campos omitidos mantêm o
    default de `Projeto`.
    """
    projeto = Projeto()
    for secao, valores in entradas.items():
        atual = getattr(projeto, secao)
        setattr(projeto, secao, replace(atual, **valores))
    return projeto


CASOS: list[CasoLiteratura] = [
    CasoLiteratura(
        id="RANK-01",
        metodo="rankine",
        fonte="fórmula fechada — Ka=tan²(45-φ/2), Ea=½KaγH² (H=4, γ=20, φ=30, c=0)",
        entradas={
            "geometria": {"altura_H_m": 4.0, "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {
                "peso_especifico_kN_m3": 20.0,
                "angulo_atrito_g": 30.0,
                "coesao_kN_m2": 0.0,
            },
            "sobrecarga": {"uniforme_q_kN_m2": 0.0},
        },
        esperado={"solicitacao_kN_m": 53.333, "inclinacao_cunha_g": 60.0},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="RANK-02",
        metodo="rankine",
        fonte="fórmula fechada com coesão — Ea=½KaγH²-2cH√Ka, z0=2c/(γ√Ka) "
        "(H=6, γ=17.5, φ=20, c=10)",
        entradas={
            "geometria": {"altura_H_m": 6.0, "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {
                "peso_especifico_kN_m3": 17.5,
                "angulo_atrito_g": 20.0,
                "coesao_kN_m2": 10.0,
            },
            "sobrecarga": {"uniforme_q_kN_m2": 0.0},
        },
        esperado={"solicitacao_kN_m": 70.417, "z0_m": 1.632},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="RANK-03",
        metodo="rankine",
        fonte="talude — Ka=cos(i)(cos(i)-√(cos²i-cos²φ))/(cos(i)+√(cos²i-cos²φ)) "
        "(i=10, φ=30)",
        entradas={
            "geometria": {"inclinacao_topo_i_g": 10.0},
            "solo_aterro": {"angulo_atrito_g": 30.0, "coesao_kN_m2": 0.0},
        },
        esperado={"Ka": 0.34952},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="COUL-01",
        metodo="coulomb",
        fonte="degenerado — θ=0, δ=0, i=0 deve coincidir com Rankine (φ=30)",
        entradas={
            "geometria": {"inclinacao_face_beta_g": 90.0, "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {"angulo_atrito_g": 30.0, "angulo_atrito_blocos_g": 0.0},
        },
        esperado={"Ka": 0.33333},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="COUL-02",
        metodo="coulomb",
        fonte="fórmula fechada geral — Ka de Coulomb (δ=15, θ=0, i=0, φ=30)",
        entradas={
            "geometria": {"inclinacao_face_beta_g": 90.0, "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {"angulo_atrito_g": 30.0, "angulo_atrito_blocos_g": 15.0},
        },
        esperado={"Ka": 0.30142},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="BISH-01",
        metodo="bishop",
        fonte="limite — talude infinito, c=0: FS→tanφ/tanβ (φ=30, β=20)",
        entradas={
            "geometria": {"inclinacao_face_beta_g": 20.0},
            "solo_aterro": {"angulo_atrito_g": 30.0, "coesao_kN_m2": 0.0},
        },
        esperado={"fator_seguranca": 1.5863},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="GEO-01",
        metodo="geossintetico",
        fonte="consistência interna — ΣTmax das camadas ≈ Ea de Rankine para a "
        "mesma geometria (H=4, γ=20, φ=30, c=0; ver PLANO_IMPLEMENTACAO.md §3.5)",
        entradas={
            "geometria": {"altura_H_m": 4.0, "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {
                "peso_especifico_kN_m3": 20.0,
                "angulo_atrito_g": 30.0,
                "coesao_kN_m2": 0.0,
            },
            "sobrecarga": {"uniforme_q_kN_m2": 0.0},
        },
        esperado={"Tmax_total_kN_m": 53.333},
        tolerancia=0.01,
    ),
    CasoLiteratura(
        id="EXT-01",
        metodo="externa",
        fonte="exemplo condutor — bloco H=4, B=5, γ=20, φ=30, c=0, q=10; "
        "fundação φ=30, c=15, γ=20; solo retido = mesmo φ=30, δ_ret=0 "
        "(ver PROMPTS_ESTABILIDADE_EXTERNA.md, Parte A)",
        entradas={
            "geometria": {"altura_H_m": 4.0, "largura_aterro_B_m": 5.0,
                          "inclinacao_topo_i_g": 0.0},
            "solo_aterro": {"peso_especifico_kN_m3": 20.0, "angulo_atrito_g": 30.0,
                            "coesao_kN_m2": 0.0},
            "solo_fundacao": {"peso_especifico_kN_m3": 20.0, "angulo_atrito_g": 30.0,
                              "coesao_kN_m2": 15.0},
            "sobrecarga": {"uniforme_q_kN_m2": 10.0},
        },
        esperado={"FS_desl": 5.02, "FS_tomb": 11.51, "FS_cap": 14.96},
        tolerancia=0.5,
    ),
    CasoLiteratura(
        id="EXT-REF-01",
        metodo="externa",
        fonte="REF — Wesley (2009), Fundamentals of Soil Mechanics, muro de "
        "solo reforçado: bloco H=9, B=3,7; aterro γ=18,2 φ=35; solo retido "
        "γ=16,8 φ=26 c=0 com δ_ret=φ_ret=26° (empuxo inclinado); φ_base = "
        "aterro reforçado (35°); sem sobrecarga",
        entradas={
            "geometria": {"altura_H_m": 9.0, "largura_aterro_B_m": 3.7},
            "solo_aterro": {"peso_especifico_kN_m3": 18.2, "angulo_atrito_g": 35.0,
                            "coesao_kN_m2": 0.0},
            "solo_encosta": {"peso_especifico_kN_m3": 16.8, "angulo_atrito_g": 26.0,
                             "coesao_kN_m2": 0.0, "angulo_atrito_blocos_g": 26.0},
            "sobrecarga": {"uniforme_q_kN_m2": 0.0},
        },
        esperado={"Pah_kN_m": 265.7, "Pav_kN_m": 129.6, "FS_desl": 1.94,
                  "FS_tomb": 2.00},
        tolerancia=1.0,
        metodo_kwargs={"fonte_phi_base": "aterro"},
    ),
]
